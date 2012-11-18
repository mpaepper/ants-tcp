for f in tron_0{0..9}.map tron_{10..99}.map
do
   ./1v1_mapgen.py > "$f"
done
