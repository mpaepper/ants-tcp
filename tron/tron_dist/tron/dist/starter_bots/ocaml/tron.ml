(* ocaml Tron starter package. Reworking of Wargame starter. *)

let out_chan = stderr (* open_out "mybot_err.log" *);;

let get_time () = Unix.gettimeofday ();;

let debug s = 
   output_string out_chan s; 
   flush out_chan
;;

type game_setup =
 {
   mutable turn : int;
   mutable rows : int;
   mutable cols : int;
   mutable player_id : int;
   mutable player_seed : int;
   mutable turntime : int;
   mutable loadtime : int;
   mutable agents_per_player : int;
 }
;;

type dir = [ `N | `E | `S | `W];;

type terrain = [ `Land | `Wall ];;

(*let `terrain = [|'.';'%'|]*)

let dir_of_string d =
   match String.lowercase d with
    | "n" -> `N
    | "e" -> `E
    | "s" -> `S
    | "w" -> `W
    | _ -> raise Not_found
;;

let string_of_dir d =
   match d with
    | `N -> "N"
    | `E -> "E"
    | `S -> "S"
    | `W -> "W"
;;


let step_unbound d (row, col) =
   match d with
    | `N -> (row - 1), col
    | `S -> (row + 1), col
    | `W -> row, (col - 1)
    | `E -> row, (col + 1)
    | `X -> row, col
;;

let rec wrap0 bound n =
   if bound < 0 then 0
   else if n < 0 then wrap0 bound (n + bound)
   else if n >= bound then wrap0 bound (n - bound)
   else n
;;

let wrap_bound (rows, cols) (row, col) =
   wrap0 rows row,
   wrap0 cols col
;;

let step_dir d bounds (row, col) =
   let new_loc = step_unbound d (row, col) in
   wrap_bound bounds new_loc
;;

let not_blocked grid (row, col) =
   grid.(row).(col) = `Land
;;

type agent =
 {
   row : int;
   col : int;
   heading : dir;
   owner : int;
 }
;;

type game_state =
 {
   setup : game_setup;
   go_time : float;
   mutable grid : terrain array array;
   mutable agent : agent list;
   mutable dead : agent list;
   mutable wall : (int * int) list;
 }
;;

let agent_loc agent = agent.row, agent.col;;

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
      gstate.agent <- [];
      gstate.dead <- [];
     )
;;

let new_agent row col heading owner =
  {
   row = row;
   col = col;
   heading = heading;
   owner = owner;
  }
;;

let add_agent gstate row col heading owner =
   gstate.agent <- new_agent row col heading owner :: gstate.agent;
   gstate.grid.(row).(col) <- `Wall
;;

let add_dead gstate row col heading owner =
   gstate.dead <- new_agent row col heading owner :: gstate.dead
;;

let init_grid gstate =
   gstate.grid <- Array.make_matrix gstate.setup.rows gstate.setup.cols `Land;
   List.iter (fun (row, col) -> gstate.grid.(row).(col) <- `Wall) gstate.wall
;;

let add_wall gstate row col =
   gstate.wall <- (row, col) :: gstate.wall
;;

let four_term gstate key t1 t2 t3 t4 =
   match key with
    | "a" -> add_agent gstate t1 t2 (dir_of_string t3) t4
    | "d" -> add_dead gstate t1 t2 (dir_of_string t3) t4
    | _ -> ()
;;

let two_term gstate key t1 t2 =
   match key with
    | "w" -> add_wall gstate t1 t2
    | _ -> ()
;;

let one_term gstate key value =
   match key with
    | "turn" -> gstate.setup.turn <- value
    | "rows" -> gstate.setup.rows <- value
    | "cols" -> gstate.setup.cols <- value
    | "player_id" -> gstate.setup.player_id <- value
    | "player_seed" -> gstate.setup.player_seed <- value
    | "loadtime" -> gstate.setup.loadtime <- value
    | "turntime" -> gstate.setup.turntime <- value
    | "agents_per_player" -> gstate.setup.agents_per_player <- value
    | _ -> ()
;;

let add_line gstate line =
   sscanf_cps "%s %d %d %s %d" (four_term gstate)
     (
      sscanf_cps "%s %d %d" (two_term gstate)
        (
         sscanf_cps "%s %d" (one_term gstate) (fun _ -> ())
        )
     )
     (uncomment line)

let update gstate lines =
   let cgstate =
      if gstate.setup.turn = 0 then gstate
      else (clear_gstate gstate; gstate)
   in
      List.iter (add_line cgstate) lines;
      if gstate.setup.turn = 0 then init_grid gstate
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

let issue_order (row, col) dir =
   Printf.printf "o %d %d %s\n" row col (string_of_dir dir)
;;

(* Print go, newline, and flush buffer *)
let finish_turn () = Printf.printf "go\n%!";;

(* End output section *)

class swrap state =
 object (self)
   val mutable state = state
   method bounds = state.setup.rows, state.setup.cols
   method get_state = state
   method set_state v = state <- v
   method issue_order loc (dir:dir) = issue_order loc dir
   method finish_turn () = finish_turn ()
   method turn = state.setup.turn
   method my_id = state.setup.player_id
   method agents = state.agent
   method my_agents = List.filter (fun a -> a.owner = state.setup.player_id) state.agent
   method dead = state.dead
   method step_dir loc (dir:dir) = step_dir dir self#bounds loc
   method not_blocked loc = not_blocked state.grid loc
 end
;;

let loop engine =
  let proto_setup =
     {
      turn = -1;
      rows = -1;
      cols = -1;
      player_id = -1;
      player_seed = -1;
      turntime = -1;
      loadtime = -1;
      agents_per_player = -1;
     }
  in
  let proto_gstate =
     {
      setup = proto_setup;
      go_time = -1.0;
      agent = [];
      dead = [];
      wall = [];
      grid = [|[| |]|]
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

