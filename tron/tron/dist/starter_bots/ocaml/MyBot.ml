(* Proposed starter logic:
 * - let focus be the most threatened friendly territory
 * - let target be the neighbor of focus with the largest army
 * - deploy all new troops into focus
 * - move all newly deployed troops into target
 *)

(* open Wargame;; *)

let threat state territory =
   List.fold_left (fun acc t ->
      if t.Wargame.owner = state#my_id then acc
      else if t.Wargame.owner = state#neutral_id then acc + 1
      else acc + 2
   ) 0 territory.Wargame.neighbors
;;

let most_threatened state =
   let _, result = List.fold_left
      (fun (prev_score, prev_t) t ->
         if not (t.Wargame.owner = state#my_id) then prev_score, prev_t
         else
            let score = threat state t in
            match prev_t with
             | None -> (score, Some t)
             | Some prev_t ->
                     if score > prev_score then (score, Some t)
                     else (prev_score, Some prev_t)
      )
      (0, None) state#territories 
   in
      result
;;

let greatest_threat state territory =
   let _, result = List.fold_left
      (fun (prev_score, prev_t) t ->
         if t.Wargame.owner = state#my_id then prev_score, prev_t
         else
            let score = threat state t in
            match prev_t with
             | None -> (score, Some t)
             | Some prev_t ->
                     if score > prev_score then (score, Some t)
                     else (prev_score, Some prev_t)
      )
      (0, None) territory.Wargame.neighbors
   in
      result
;;

let mybot_engine state =
   if state#turn = 0 then state#finish_turn ()
   else
    (
      let focus = most_threatened state in
      begin match focus with | None -> () | Some focus ->
         let myself = state#myself in
         let to_place = myself.Wargame.armies_to_place in
         Wargame.issue_order_deploy to_place focus;
         let target = greatest_threat state focus in
            begin match target with | None -> () | Some target ->
               Wargame.issue_order_move to_place focus target
            end;
      end;
      state#finish_turn ()
    )
;;

Wargame.loop mybot_engine;;

