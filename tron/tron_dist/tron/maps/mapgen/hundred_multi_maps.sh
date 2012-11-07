for f in tron_multi_0{0..9}.map tron_multi_{10..99}.map
do
   ./symmetric_mapgen.py > "$f"
done
