"""Propeller MPK read-only extractor. Layout verified against GARbro ArcMPK.cs."""
import struct,json,sys
from pathlib import Path
def entries(path):
 b=Path(path).read_bytes();off,n=struct.unpack_from('<II',b);idx=b[off:off+n*40];key=idx[31];idx=bytes(x^key for x in idx)
 for i in range(n):
  name=idx[i*40:i*40+32].split(b'\0')[0].decode('cp932').lstrip('\\');pos,size=struct.unpack_from('<II',idx,i*40+32)
  assert pos+size<=len(b)
  data=b[pos:pos+size]
  if name.lower().endswith('.msc') and data[0]==0x88:data=bytes(x^0x88 for x in data)
  yield name,pos,size,data
if __name__=='__main__':
 src,dst=map(Path,sys.argv[1:3]);dst.mkdir(parents=True,exist_ok=True)
 rows=[]
 for name,pos,size,data in entries(src):
  assert '/' not in name and '\\' not in name and '..' not in name
  (dst/name).write_bytes(data);rows.append(dict(name=name,offset=pos,size=size))
 (dst/'index.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2))
 print(len(rows),'files extracted')
