;;;; main.lisp

(load "parse-number.lisp")
(load "asteroids.lisp")

;;; Functions

;; This is the actual 'AI'.  Very simple currently: loops through each of your
;; ants and issues an order to go either north, east, south or west if the tile
;; in the direction is not a water tile.
(defun do-turn ()
  (let* ((my-ship (my-ship *state*))
         (mx (getf my-ship :x))
         (my (getf my-ship :y))
         (mdir (getf my-ship :heading))
         (mdx (getf my-ship :dx))
         (mdy (getf my-ship :dy))
         (gun-intersect (ray-intersects mx my mdir))
         (vec-intersect (ray-intersects mx my (atan mdy mdx)))
         (thrust 0)
         (turn 0)
         (fire 0))
    ;; make sure we're moving
    (when (and (= mdx 0) (= mdy 0))
      (setf thrust 1.0))
    ;; shoot when another ship is in line-of-sight
    (when (and gun-intersect (getf gun-intersect :id))
      (setf fire 1))
    ;; static turn to avoid asteroids & ships
    (when vec-intersect
      (setf thrust 1.0
            turn 1.0))
    (issue-order thrust turn fire)))


(defun main ()
  "Main game loop: parses the (initial) game state and calls DO-TURN and
  FINISH-TURN."
  (handler-bind ((sb-sys:interactive-interrupt #'user-interrupt))
    (loop while (handler-case (peek-char nil *standard-input* nil)
                  (sb-int:simple-stream-error nil))
          for end-of-game-p = (parse-game-state)
          when end-of-game-p do (loop-finish)
          do (when (> (turn *state*) 0)
               (do-turn))
             (finish-turn))))
