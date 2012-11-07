open Tron;;

let rec try_steps state agent dirs =
   match dirs with [] -> ()
   | d :: tail ->
        if state#not_blocked(state#step_dir (agent_loc agent) d) then
           state#issue_order (agent_loc agent) d
        else try_steps state agent tail
;;

(* step_agent makes use of the try_steps function to test all of the 
options in order, and take the first one found; otherwise, does 
nothing. *)

let step_agent state agent =
   try_steps state agent [`N; `E; `S; `W]
;;

(* This steps through a list of agents using tail recursion and attempts 
to order all of them to move. *)

let rec step_agents state my_l =
   match my_l with
    | [] -> ()
    | head :: tail ->
         step_agent state head;
         step_agents state tail
;;

(* The bot checks whether it's Turn 0 (setting up turn, no orders 
allowed) and finishes the turn immediately if it is; otherwise it calls 
step_agents. *)

let mybot_engine state =
   if state#turn = 0 then state#finish_turn ()
   else
    (
      step_agents state state#my_agents;
      state#finish_turn ()
    )
;;

loop mybot_engine;;

