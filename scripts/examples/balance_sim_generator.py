import json, sys
# usage: mk_sim2.py ROUNDS OUT '{"mother":800,...}'   (player is AI-controlled so the human side is not handicapped)
n = int(sys.argv[1]); out = sys.argv[2]; tune = sys.argv[3] if len(sys.argv) > 3 else "{}"
js = ("(()=>{Object.assign(TUNE,%s);const r=[];for(let k=0;k<%d;k++){round();let t=0,t3=-1;while(phase==='play'&&t<400){for(const a of A)ai(a,1/60);rules(1/60);t+=1/60;"
      "if(t3<0&&A.filter(a=>a.zom).length>=3)t3=t}r.push({w:fm,z:A.filter(a=>a.zom).length,t:Math.round(t),t3:t3<0?-1:Math.round(t3)})}"
      "const zw=r.filter(x=>x.w==='ZOMBIES WIN').length,med=a=>a.length?a.sort((x,y)=>x-y)[a.length>>1]:-1;"
      "return 'ZW '+zw+'/%d | round med '+med(r.map(x=>x.t))+'s | to-3-zombies med '+med(r.filter(x=>x.t3>0).map(x=>x.t3))+'s | fizzled '+r.filter(x=>x.t3<0).length+' | humans left in HS rounds '+r.filter(x=>x.w!=='ZOMBIES WIN').map(x=>10-x.z).join(',')})()") % (tune, n, n)
json.dump([{"do":"eval","js":"document.querySelector('button[data-m=zm]').click(),1","label":"start"},{"do":"wait_for","js":"state==='play'","timeout":5000},
           {"do":"eval","js":js,"label":"RESULT"}], open(out, "w"))
