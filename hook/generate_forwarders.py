from pathlib import Path
import json,sys
root=Path(__file__).resolve().parent
output=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else root/'build'
output.mkdir(parents=True,exist_ok=True)
exports=json.loads((root/'winmm-exports.json').read_text())['exports']
header=['/* All exports from the validated Proton WinMM, including ordinals. */',f'#define EXPORT_COUNT {len(exports)}','void *forward[EXPORT_COUNT];','static const char *names[]={']
header += [('"'+r['name']+'",') if r['name'] else f'(const char*){r["ordinal"]},' for r in exports];header+=['};']
asm=['.intel_syntax noprefix','.text'];defs=['LIBRARY winmm.dll','EXPORTS']
for i,r in enumerate(exports):
 asm += [f'.globl _proxy_{i}',f'_proxy_{i}:',' pushfd',' cmp dword ptr [_initialized],2',f' je ready_{i}',' pushad',' call _init',' popad',f'ready_{i}:',' popfd',f' jmp dword ptr [_forward+{i*4}]']
 defs += [f' {r["name"] or "ordinal_"+str(r["ordinal"])}=proxy_{i} @{r["ordinal"]}'+(' NONAME' if r['name'] is None else '')]
(output/'winmm-exports.h').write_text('\n'.join(header)+'\n');(output/'forwarders.s').write_text('\n'.join(asm)+'\n');(output/'winmm.def').write_text('\n'.join(defs)+'\n')
