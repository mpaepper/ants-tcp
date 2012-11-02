;;;; asteroids.lisp

;;; State Class

(defclass state ()
  ((width           :reader width           :initform nil)
   (height          :reader height          :initform nil)
   (player-id       :reader player-id       :initform nil)
   (turn            :reader turn            :initform nil)
   (asteroids       :reader asteroids       :initform nil)
   (bullets         :reader bullets         :initform nil)
   (ships           :reader ships           :initform nil)
   (my-ship         :reader my-ship         :initform nil)
   (my-goal-dir     :accessor my-goal-dir   :initform 0)
   (load-time       :reader load-time       :initform nil)
   (turn-time       :reader turn-time       :initform nil)
   (turn-start-time :reader turn-start-time :initform nil)
   (turns           :reader turns           :initform nil)))


;;; Globals

(defvar *state* (make-instance 'state))


;;; Functions

(defun asteroid-radius (asteroid)
  (expt (+ (getf asteroid :category) 1) 2))


(defun distance (x1 y1 x2 y2)
  (let ((dx (- x2 x1))
        (dy (- y2 y1)))
    (sqrt (+ (* dx dx) (* dy dy)))))


(defun finish-turn ()
  "Prints the \"finish turn\" string to standard output."
  (format *standard-output* "~&go~%")
  (force-output *standard-output*))


(defun issue-order (thrust turn fire)
    (format *standard-output* "~&o ~F ~F ~D~%" thrust turn fire))


(defun mkstr (&rest args)
  (with-output-to-string (s)
    (dolist (a args)
      (princ a s))))


(defun par-value (string)
  "Helper function for parsing game state input from the server."
  (parse-number:parse-number (subseq string (position #\space string)
                                     (length string))))


(defun parse-asteroid (line)
  (let* ((split (split-string line))
         (category (parse-number:parse-number (elt split 1)))
         (x (parse-number:parse-number (elt split 2)))
         (y (parse-number:parse-number (elt split 3)))
         (heading (parse-number:parse-number (elt split 4))))
    (list :category category :x x :y y :heading heading)))


(defun parse-bullet (line)
  (let* ((split (split-string line))
         (owner (parse-number:parse-number (elt split 1)))
         (x (parse-number:parse-number (elt split 2)))
         (y (parse-number:parse-number (elt split 3)))
         (heading (parse-number:parse-number (elt split 4))))
    (list :owner owner :x x :y y :heading heading)))


(defun parse-game-parameters ()
  "Parses turn 0 game parameters and sets them in *STATE*.  Also creates
  initial game map and assigns it to (GAME-MAP *STATE*)."
  (loop for line = (read-line *standard-input* nil)
        until (starts-with line "ready")
        do (cond ((starts-with line "width")
                  (setf (slot-value *state* 'width) (par-value line)))
                 ((starts-with line "height ")
                  (setf (slot-value *state* 'height) (par-value line)))
                 ((starts-with line "player_id ")
                  (setf (slot-value *state* 'player-id) (par-value line)))
                 ((starts-with line "loadtime ")
                  (setf (slot-value *state* 'load-time)
                        (/ (par-value line) 1000.0)))
                 ((starts-with line "turntime ")
                  (setf (slot-value *state* 'turn-time)
                        (/ (par-value line) 1000.0)))
                 ((starts-with line "turns ")
                  (setf (slot-value *state* 'turns) (par-value line))))))


(defun parse-game-state ()
  "Calls either PARSE-TURN or PARSE-GAME-PARAMETERS depending on the line
  on standard input.  Modifies *STATE* and returns T if the game has ended,
  otherwise NIL."
  (setf (slot-value *state* 'turn-start-time) (wall-time))
  (loop for line = (read-line *standard-input* nil)
        until (> (length line) 0)
        finally (return (cond ((starts-with line "end")
                               (parse-turn)
                               t)
                              ((starts-with line "turn 0")
                               (setf (slot-value *state* 'turn) 0)
                               (parse-game-parameters)
                               nil)
                              ((starts-with line "turn ")
                               (setf (slot-value *state* 'turn)
                                     (par-value line))
                               (parse-turn)
                               nil)))))


(defun parse-player (line)
  (let* ((split (split-string line))
         (player-id (parse-number:parse-number (elt split 1)))
         (x (parse-number:parse-number (elt split 2)))
         (y (parse-number:parse-number (elt split 3)))
         (heading (parse-number:parse-number (elt split 4)))
         (dx (parse-number:parse-number (elt split 5)))
         (dy (parse-number:parse-number (elt split 6))))
    (list :id player-id :x x :y y :heading heading :dx dx :dy dy)))


(defun parse-turn ()
  "Parses a typical turn.  Modifies *STATE*."
  (setf (slot-value *state* 'asteroids) nil
        (slot-value *state* 'bullets)   nil
        (slot-value *state* 'ships)     nil
        (slot-value *state* 'my-ship)   nil)
  (loop for line = (read-line *standard-input* nil)
        until (starts-with line "go")
        do (cond ((starts-with line "a ")
                  (push (parse-asteroid line) (slot-value *state* 'asteroids)))
                 ((starts-with line "b ")
                  (push (parse-bullet line) (slot-value *state* 'bullets)))
                 ((starts-with line "p ")
                  (let ((player (parse-player line)))
                    (push player (slot-value *state* 'ships))
                    (when (= (player-id *state*) (getf player :id))
                      (setf (slot-value *state* 'my-ship) player)))))))


(defun ray-intersects (x y direction &key (length nil) (stop-at-hit t))
  "DIRECTION in radians."
  (let ((x-step (* 2 (cos direction)))
        (y-step (* 2 (sin direction)))
        result)
    (unless length
      (setf length (- (sqrt (+ (* (width *state*) (width *state*))
                               (* (height *state*) (height *state*))))
                      10)))
    (loop with dx = (* 3 x-step)
          with dy = (* 3 y-step)
          until (>= (distance 0 0 dx dy) length)
          for rx = (+ x dx)
          for ry = (+ y dy)
          do (loop for a in (asteroids *state*)
                   do (when (<= (distance rx ry (getf a :x) (getf a :y))
                                (asteroid-radius a))
                        (push a result)
                        (when stop-at-hit
                          (loop-finish))))
             (loop for s in (ships *state*)
                   do (when (<= (distance rx ry (getf s :x) (getf s :y))
                                5)
                        (push s result)
                        (when stop-at-hit
                          (loop-finish))))
             (incf dx x-step)
             (incf dy y-step))
    (if stop-at-hit
        (car result)
        result)))


;; TODO needs a docstring
(defun split-string (string)
  (loop with result = nil
        with value = nil
        for c across string
        when (and (char= c #\space) value)
          do (push (coerce (nreverse value) 'string) result)
             (setf value nil)
        when (char/= c #\space)
          do (push c value)
        finally (when value
                  (push (coerce (nreverse value) 'string) result))
                (return (nreverse result))))


(defun starts-with (sequence subsequence)
  (let ((sublen (length subsequence)))
    (when (and (> sublen 0)
               (<= sublen (length sequence)))
      (equal (subseq sequence 0 sublen) subsequence))))


(defun user-interrupt (arg)
  (declare (ignore arg))
  (format *debug-io* "~&User interrupt. Aborting...~%")
  (quit))


(let ((time-units (/ 1.0 internal-time-units-per-second)))
  ;; TODO correctly name function: doesn't return wall time
  ;; TODO use DOUBLE-FLOATs?
  (defun wall-time (&key (offset 0))
    "Returns the time in seconds (as a FLOAT) since SBCL was started."
    (+ (* (get-internal-real-time) time-units)
       offset)))
