(* ocaml Wargame starter package. Reworking of Asteroids starter. *)

let out_chan = stderr (* open_out "mybot_err.log" *);;

let get_time () = Unix.gettimeofday ();;

let debug s = 
   output_string out_chan s; 
   flush out_chan
;;

type game_setup =
 {
   mutable turn : int;
   mutable width : int;
   mutable height : int;
   mutable player_id : int;
   mutable player_seed : int;
   mutable turntime : int;
   mutable loadtime : int;
   mutable neutral_id : int;
 }
;;

type player =
 {
   p_id : int;
   armies_to_place : int;
 }
;;

type territory =
 {
   t_id : int;
   group : int;
   owner : int;
   armies : int;
   mutable neighbors : territory list;
 }
;;

type connection =
 {
   connect_from : int;
   connect_to : int
 }
;;

type game_state =
 {
   setup : game_setup;
   go_time : float;
   mutable territories : territory list;
   mutable connections : connection list;
   mutable players : player list;
 }
;;

let rec connect territories = function
 | [] -> ()
 | c :: tail ->
      let a = List.find (fun t -> t.t_id = c.connect_from) territories in
      let b = List.find (fun t -> t.t_id = c.connect_to) territories in
         a.neighbors <- b :: a.neighbors;
         b.neighbors <- a :: b.neighbors;
      connect territories tail
;;

let make_connections gstate =
   connect gstate.territories gstate.connections
;;

(* type order = (float * float * int);; *)

(* Begin input processing stuff *)

let uncomment s =
  try String.sub s 0 (String.index s '#')
  with Not_found -> s
;;

let sscanf_cps fmt cont_ok cont_fail s =
  try Scanf.sscanf s fmt cont_ok
  with _ -> cont_fail s
;;

let clear_gstate gstate =
   if gstate.setup.turn < 1 then () else
     (
      gstate.territories <- [];
      gstate.connections <- [];
      gstate.players <- [];
     )
;;

let add_connection gstate t1 t2 =
   let c = {connect_from = t1; connect_to = t2} in
      gstate.connections <- c :: gstate.connections
;;

let add_territory gstate t1 t2 t3 t4 =
   let t = {t_id = t1; group = t2; owner = t3; armies = t4; neighbors = []} in
      gstate.territories <- t :: gstate.territories
;;

let add_player gstate t1 t2 =
   let p = {p_id = t1; armies_to_place = t2} in
      gstate.players <- p :: gstate.players
;;

let six_term gstate key t1 t2 t3 t4 t5 t6 =
   match key with
    | "t" -> add_territory gstate t1 t2 t5 t6
    | _ -> ()
;;

let three_term gstate key t1 t2 t3 =
   match key with
    | "p" -> add_player gstate t1 t3 (*FIXME redundant*)
    | _ -> ()
;;

let two_term gstate key t1 t2 =
   match key with
    | "c" -> add_connection gstate t1 t2
    | "p" -> add_player gstate t1 t2
    | _ -> ()
;;

let one_term gstate key value =
   match key with
    | "turn" -> gstate.setup.turn <- value
    | "width" -> gstate.setup.width <- value
    | "height" -> gstate.setup.height <- value
    | "player_id" -> gstate.setup.player_id <- value
    | "player_seed" -> gstate.setup.player_seed <- value
    | "loadtime" -> gstate.setup.loadtime <- value
    | "turntime" -> gstate.setup.turntime <- value
    | "neutral_id" -> gstate.setup.neutral_id <- value
    | _ -> ()
;;

let add_line gstate line =
   sscanf_cps "%s %d %d %d %d %d %d" (six_term gstate)
     (
      sscanf_cps "%s %d %d %d" (three_term gstate)
        (
         sscanf_cps "%s %d %d" (two_term gstate)
           (
            sscanf_cps "%s %d" (one_term gstate) (fun _ -> ())
           )
        )
     )
     (uncomment line)

let update gstate lines =
   let cgstate =
      if gstate.setup.turn = 0 then gstate
      else (clear_gstate gstate; gstate)
   in
      List.iter (add_line cgstate) lines;
      make_connections cgstate
;;

let read_lines () =
  let rec read_loop acc =
    let line = read_line () in
    if String.length line >= 2 && String.sub line 0 2 = "go" 
    || String.length line >= 3 && String.sub line 0 3 = "end"
    || String.length line >= 5 && String.sub line 0 5 = "ready" then
     (
      List.rev acc
     )
    else
      read_loop (line :: acc)
  in
  try Some (read_loop []) with End_of_file -> None
;;

let read gstate =
  let ll = read_lines () in
  let go_time = get_time () in
  match ll with
  | Some lines -> Some {(update gstate lines; gstate) with go_time = go_time}
  | None -> None
;;

(* End input section *)

(* Begin output section *)

let issue_order_deploy num target =
   Printf.printf "o d %d %d\n" num target.t_id
;;

let issue_order action num source target =
   Printf.printf "o %s %d %d %d\n" action num source.t_id target.t_id
;;

let issue_order_move num source target =
   issue_order "m" num source target
;;

let issue_order_attack num source target =
   issue_order "a" num source target
;;

let issue_order_transfer num source target =
   issue_order "t" num source target
;;

(* Print go, newline, and flush buffer *)
let finish_turn () = Printf.printf "go\n%!";;

(* End output section *)

class swrap state =
 object (self)
   val mutable state = state
   method get_state = state
   method set_state v = state <- v
   method issue_order o = issue_order o
   method finish_turn () = finish_turn ()
   method turn = state.setup.turn
   method my_id = state.setup.player_id
   method myself = 
      List.find (fun p -> p.p_id = state.setup.player_id) state.players
   method neutral_id = state.setup.neutral_id
   method territories = state.territories
 end
;;

let loop engine =
  let proto_setup =
     {
      turn = -1;
      width = -1;
      height = -1;
      player_id = -1;
      player_seed = -1;
      turntime = -1;
      loadtime = -1;
      neutral_id = -1;
     }
  in
  let proto_gstate =
     {
      setup = proto_setup;
      go_time = -1.0;
      territories = [];
      connections = [];
      players = []
     }
  in
  let wrap = new swrap proto_gstate in
  let rec take_turn i gstate =
    match read gstate with
    | Some state ->
        begin try
         (
          wrap#set_state state;
          engine wrap;
          flush stdout;
         )
        with exc ->
         (
          debug (Printf.sprintf
             "Exception in turn %d :\n" i);
          debug (Printexc.to_string exc);
          raise exc
         )
        end;
        take_turn (i + 1) wrap#get_state
    | None ->
        ()
  in
     take_turn 0 proto_gstate
;;

