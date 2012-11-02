let mybot_engine state =
   if state#turn = 0 then state#finish_turn ()
   else
    (
(*      Tron.issue_order (0.05, -0.15, 1); *)
      state#finish_turn ()
    )
;;

Tron.loop mybot_engine;;


