		replay_data = ## REPLAY PLACEHOLDER ##;
		
		//~ im = {
			//~ "p0" : "visualizer/p0.png",
			//~ "p1" : "visualizer/p1.png",
			//~ "a0" : "visualizer/a0.png",
			//~ "a1" : "visualizer/a1.png",
			//~ "a2" : "visualizer/a2.png",
			//~ "a3" : "visualizer/a3.png",
			//~ "a4" : "visualizer/a2.png",
			//~ "b0" : "visualizer/b0.png",
			//~ "b1" : "visualizer/b1.png",
		//~ }
		C = document.getElementById('C')
		V = C.getContext('2d');
		the_turn = 0
		var color = new Array(9);
		color[0] = 'cyan';
		color[1] = 'green';
		color[2] = 'blue';
		color[3] = 'yellow';
		color[4] = 'red';
		color[5] = 'magenta';
		color[6] = 'darkgray';
		color[7] = 'purple';
		color[8] = 'white';
		function init() {
			width  = replay_data["replaydata"]["width"]
			height = replay_data["replaydata"]["height"]
			nturns = replay_data["replaydata"]["data"].length
			player = replay_data["replaydata"]["players"]
			scores = replay_data["replaydata"]["scores"]
			sx = 600 / width
			sy = 600 / height
			//~ for ( i in im ) {
				//~ s = im[i]
				//~ im[i] = new Image()
				//~ im[i].src = s
			//~ }
			play()
		}
		function clear() {
			V.fillStyle = 'black'
			V.fillRect(0,0,600,600)
		}
		function draw_frame(f) {
			clear()
			frame = replay_data["replaydata"]["data"][f]
			V.fillStyle = 'white'
			V.strokeStyle = 'white'
			info = "turn "+the_turn + "  ["
			for ( i=0; i<player; i++ ) {
				info += scores[i][the_turn] 
				if (i !=player-1)
					info += ","
			}
			info += "]"
			V.fillText(info, 260,10)
			for (i in frame) {
				var index = frame[i][1];
				if (frame[i][0] == 't'){
					index = frame[i][5];
					img = frame[i][1] + ":"
					if (index > 7)
						{index = 8;
						img += "n:"}
					else img += frame[i][5] + ":";
					V.fillStyle = color[index]
					V.strokeStyle = 'white'
					img += frame[i][6]
					x = frame[i][3] * sx
					y = frame[i][4] * sy
					end_arc = (frame[i][0]=="p" ? (frame[i][4] - (Math.PI * 2 / 3)): 0 )
					begin_arc = (frame[i][0]=="p" ? (frame[i][4] + (Math.PI * 2 / 3)): Math.PI * 2 )
					r = 5
					V.fillText(img, x,y)
					V.beginPath();
					V.arc(x,y, r*sx,begin_arc,end_arc,true);
					V.closePath();
					V.stroke();
					}
			}
		}
        function stop() {
            clearInterval(tick)
            tick=-1
        }
        function back() {
            stop()
            if ( the_turn > 0 ) 
                the_turn -= 1
            draw_frame(the_turn)
        }
        function forw() {
            stop()
            if ( the_turn < nturns-1 ) 
                the_turn += 1
            draw_frame(the_turn)
        }
        function pos(t) {
            stop()
            the_turn = t
            draw_frame(the_turn)
        }
        function play() {
            tick = setInterval( function() {
                if (the_turn < nturns)
                {
                    draw_frame(the_turn)
                    the_turn += 1
                } else {
                    stop()
                }
            },200)
        }
		init()
