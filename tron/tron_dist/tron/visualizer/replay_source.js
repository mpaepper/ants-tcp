//		replay_data = ## REPLAY PLACEHOLDER ##;
		replay_data = {"status": ["eliminated", "eliminated"]};
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
		C = document.getElementById('C');
		V = C.getContext('2d');
		the_turn = 0;
		Array.prototype.set_color=function(r, g, b)
		{
			this[0] = r;
			this[1] = g;
			this[2] = b;
		}
		var color = new Array(10);
		for (i=0;i<10;i++) {
			color[i] = new Array(3);
			color[i].set_color(255, 0, 0);
		}
		color[0].set_color(0, 0, 255);
		color[1].set_color(0, 255, 0);
		color[2].set_color(255, 255, 0);
		color[3].set_color(128, 255, 128);
//		color[0] = 'green';
//		color[1] = 'blue';
//		color[2] = 'cyan';
//		color[3] = 'yellow';
//		color[4] = 'magenta';
//		color[5] = 'purple';
//		color[6] = 'white';
//		color[7] = 'darkgray';
//		color[8] = 'red';
		color[0] = 
		function init() {
			width  = replay_data["replaydata"]["width"];
			height = replay_data["replaydata"]["height"];
			nturns = replay_data["replaydata"]["data"].length;
			player = replay_data["replaydata"]["players"];
			scores = replay_data["replaydata"]["scores"];
			water = replay_data["replaydata"]["water"];
			sx = 600 / width;
			sy = 600 / height;
			//~ for ( i in im ) {
				//~ s = im[i]
				//~ im[i] = new Image()
				//~ im[i].src = s
			//~ }
			play();
		}
		function clear() {
			V.fillStyle = 'black';
			V.fillRect(0,0,600,600);
		}
		function draw_frame(f) {
			clear()
			for (w_index=0; w_index < water.length; w_index++) {
				w = water[w_index]
				row = w[0]
				col = w[1]
				x = col * sx
				y = row * sy
				V.fillStyle = 'darkgray'
				V.fillRect(x,y,sx,sy)
			}
			for (iter_frame=0;iter_frame<f;iter_frame++) {
				frame = replay_data["replaydata"]["data"][iter_frame]
				for (i in frame) {
					x = frame[i][2] * sx
					y = frame[i][1] * sy
					if (frame[i][0] == 'a')
					{
						var index = frame[i][4];
						alpha = 196
						V.fillStyle = transp_color(index, alpha);
						V.fillRect(x,y,sx,sy)
					}
					else if (frame[i][0] == 'd')
					{
						var index = frame[i][4];
						V.fillStyle = 'red';
						V.fillRect((x + sx / 4), (y + sy / 4) ,(sx / 2), (sy / 2))
					}
//					V.strokeStyle = color[index]
//					V.fillStyle = 'white'
//					V.strokeStyle = 'white'
//					V.fillRect(10, 10, 10, 10)
//					img = frame[i][0] + frame[i][1]
//					a = frame[i][4]
//					end_arc = (frame[i][0]=="p" ? (frame[i][4] - (Math.PI * 2 / 3)): 0 )
//					begin_arc = (frame[i][0]=="p" ? (frame[i][4] + (Math.PI * 2 / 3)): Math.PI * 2 )
	
//					r = (frame[i][0]=="b" ? 2 :(frame[i][0]=="p" ? 5 : (frame[i][1]+1)*(frame[i][1]+1)))
				//~ V.rotate(r)
				//~ V.translate(x,y)
//					V.fillText(img, x,y)
//					V.beginPath();
//					V.arc(x,y, r*sx,begin_arc,end_arc,true);
//					V.closePath();
//					V.stroke();
				//~ V.translate(-x,-y)
				//~ if ( im[img] && im[img].data )
					//~ V.drawImage(im[img], x,y)
				//~ V.rotate(-r)
				}
			}
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
		}
        function transp_color(index, alpha) {
		return (color[index][0], color[index][1], color[index][2], alpha)
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
