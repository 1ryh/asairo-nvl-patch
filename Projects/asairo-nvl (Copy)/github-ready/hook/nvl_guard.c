/* Target-specific scenario pagination guard. Native rendering is unchanged. */
typedef unsigned char U8; typedef unsigned short U16; typedef unsigned int U32;
typedef unsigned long DWORD; typedef int BOOL; typedef void *HANDLE; typedef unsigned short WCHAR;
#define API __declspec(dllimport) __stdcall
HANDLE API GetModuleHandleW(const WCHAR*); HANDLE API LoadLibraryW(const WCHAR*);
U32 API GetSystemDirectoryW(WCHAR*,U32); HANDLE API GetProcAddress(HANDLE,const char*);
BOOL API VirtualProtect(void*,U32,DWORD,DWORD*); BOOL API FlushInstructionCache(HANDLE,const void*,U32);
HANDLE API VirtualAlloc(void*,U32,DWORD,DWORD);
HANDLE API GetCurrentProcess(void); long API InterlockedCompareExchange(volatile long*,long,long);
void API Sleep(DWORD); void API ExitProcess(U32); BOOL API DisableThreadLibraryCalls(HANDLE);
HANDLE API CreateFileA(const char*,DWORD,DWORD,void*,DWORD,DWORD,HANDLE);
BOOL API WriteFile(HANDLE,const void*,DWORD,DWORD*,void*); BOOL API CloseHandle(HANDLE);
U32 API GetEnvironmentVariableA(const char*,char*,U32);
static HANDLE own,real; volatile long initialized; static U8 *image;
#include "winmm-exports.h"
typedef void (__thiscall *PREP)(U8*,U8*,U32,int);
typedef void (__thiscall *OPCODE)(void*,U8*);
typedef void (__stdcall *SAVE)(U8*,U32);
static SAVE save_snapshot;
static U8 *prefix_engine,prefix_original[72],prefix_inline[72];
static U32 prefix_start,prefix_length;
static PREP prepare; static OPCODE message_opcode; static U8 clear_vm[0x204c],clear_code=6;
static HANDLE trace,state_trace; static U32 sequence;
static void zero(void *p,U32 n){U8*b=p;while(n--)*b++=0;}
static void copy(U8*d,const U8*s,U32 n){while(n--)*d++=*s++;}
static int equal(const U8*a,const U8*b,U32 n){while(n--)if(*a++!=*b++)return 0;return 1;}
static U32 read32(const void*p){return *(const U32*)p;}
static int field(U8 *engine,U32 offset){return *(int*)(engine+offset);}
static U32 bounded_length(const U8 *s,U32 cap){U32 n=0;while(n<cap&&s[n])n++;return n;}
static int ordinary_nvl(U8 *engine){return field(engine,0xfb09c)==1 && field(engine,0xf2b4c)==80 && field(engine,0xf2b50)==58 && field(engine,0xf2b54)==25 && field(engine,0xf2318)==50 && field(engine,0xf231c)==13;}
/* Name parsing and backlog/voice capture have already finished. Reuse the
   native visible-name field, never the alternate identity/voice field.
   Place a complete CP932 label immediately before the body, without moving
   any body bytes or changing saved-page/source/history strings. */
static void show_visible_name(U8 *engine){
 U8 *name=engine+0x93f00c,*open=engine+0xf230c,*close=engine+0xf2310,*dst;
 U32 n=bounded_length(name,64),a=bounded_length(open,4),b=bounded_length(close,4);
 U32 body=read32(engine+0x93f008),i,total=n+a+b;
 if(!ordinary_nvl(engine)||!n||n==64||!a||a==4||!b||b==4||body>1023||total>body)return;
 prefix_engine=engine;prefix_start=body-total;prefix_length=total;
 copy(prefix_original,engine+0x93ec08+prefix_start,total);
 dst=engine+0x93ec08+body-total;
 for(i=0;i<a;i++)*dst++=open[i];for(i=0;i<n;i++)*dst++=name[i];for(i=0;i<b;i++)*dst++=close[i];
 copy(prefix_inline,engine+0x93ec08+prefix_start,total);
 *(U32*)(engine+0x93f008)=body-total;
}
/* SaveScenarioSnapshot copies the CURRENT display scratch to its serialized
   current-message field. Temporarily restore only the prefix bytes we changed.
   The original save function retains complete control of serialization. */
static void __stdcall guarded_save(U8 *engine,U32 filename){
 U32 length=prefix_length,start=prefix_start;
 int restore=engine==prefix_engine && length && equal(engine+0x93ec08+start,prefix_inline,length);
 if(restore)copy(engine+0x93ec08+start,prefix_original,length);
 save_snapshot(engine,filename);
 if(restore && engine==prefix_engine && prefix_length==length && prefix_start==start)
  copy(engine+0x93ec08+start,prefix_inline,length);
}
static void status(const char*s,U32 n){DWORD written;HANDLE h=CreateFileA("nvl-hook-status.txt",0x40000000,1,0,2,0x80,0);if(h!=(HANDLE)-1){WriteFile(h,s,n,&written,0);CloseHandle(h);}}
/* Bound only reserves vertical space. It does not insert or choose line breaks.
   Count the ORIGINAL bytes, including markup/ruby/name overhead, at a deliberately
   narrower 20-fullwidth-cell measure than the native 25-column renderer, plus one
   slack row. Recognize explicit breaks only at CP932 character boundaries. */
static U32 reserve_rows(const U8 *s){
 U32 n=0,breaks=0;
 while(s[n] && n<1023){
  U8 c=s[n];
  if((c>=0x80 && c<0xa0)||c>=0xe0){if(!s[n+1])break;n+=2;continue;}
  if((c=='_'&&s[n+1]=='r')||(c=='\\'&&s[n+1]=='n'))breaks++;
  n++;
 }
 return (n+39)/40+breaks+1;
}
/* Recognize ONLY the exact prefix rewrite made by the earlier inline-name
   prototype. Native saved current-message ID can be zero, while the raw page
   slot retains its actual scenario ID. Require byte-for-byte unchanged body. */
static U32 delimiter_end(const U8*s,U32 at,U32 limit,const U8*end,U32 size){
 while(at+size<=limit){
  if(equal(s+at,end,size))return at+size;
  if((s[at]>=0x80&&s[at]<0xa0)||s[at]>=0xe0)at+=2;else at++;
 }
 return 0;
}
static int original_or_legacy_prefix(U8*engine,const U8*original,const U8*display){
 U32 n=bounded_length(original,1000),m=bounded_length(display,1000);
 U8*open=engine+0xf230c,*close=engine+0xf2310;
 U32 a=bounded_length(open,4),b=bounded_length(close,4),first,body,start;
 if(!n||n==1000||n!=m)return 0;
 if(equal(original,display,n+1))return 1;
 if(!a||a==4||!b||b==4||!equal(original,open,a))return 0;
 first=delimiter_end(original,a,n,close,b);
 if(!first||first>72||first+a+1>n||original[first]!='/'||!equal(original+first+1,open,a))return 0;
 body=delimiter_end(original,first+1+a,n,close,b);
 if(!body||body<first)return 0;start=body-first;
 return equal(original,display,start)&&equal(original,display+start,first)&&equal(original+body,display+body,n-body+1);
}
/* ECX=text; EDX unused; stack=(engine,id,record_history). Fastcall wrapper has
   the same stack cleanup (12 bytes) as the original thiscall. The compiler
   preserves EBX/ESI/EDI/EBP. Original preparation is called exactly once. */
static void __fastcall guarded_prepare(U8 *text,void *unused,U8 *engine,U32 id,int history){
 U32 rows=0;int before=field(engine,0xfb0a0),cleared=0;
 (void)unused;
 U32 caller=(U32)((U8*)__builtin_return_address(0)-image);
 int live=caller==0x4d461;
 /* A prototype save may contain a display-modified current-message prefix.
    Native raw page records are separate and intact. At the reviewed load
    current-message caller only, reparse the matching last raw page record. */
 if(caller==0x4e3e1 && ordinary_nvl(engine)){
  U32 count=read32(engine+0xfb11c);
  if(count>0 && count<=50 && (id==0 || read32(engine+0x101390+(count-1)*4)==id)){
   U8 *canonical=engine+0x101458+(count-1)*1000;
   if(original_or_legacy_prefix(engine,canonical,text))text=canonical;
  }
 }
 prefix_length=0;
 if(live && ordinary_nvl(engine)){
  rows=reserve_rows(text);
  if(before>0 && (U32)before+rows>13){
   /* 06 02 queues the upcoming voice in the next saved-page slot BEFORE
      05 00 prepares its text. Carry that slot across the native clear. */
   U8 pending_voice[500];U32 index=read32(engine+0xfb11c),pending_kind=0;
   int pending_valid=index<50;
   if(pending_valid){copy(pending_voice,engine+0xfb120+index*500,500);pending_kind=read32(engine+0x1012c8+index*4);}
   *(U32*)(clear_vm+0xc)=0;
   message_opcode(clear_vm,engine);
   if(pending_valid){copy(engine+0xfb120,pending_voice,500);*(U32*)(engine+0x1012c8)=pending_kind;} /* native 05 06: surface + cursor + saved-page records */
   cleared=1;
  }
 }
 if(live && trace && trace!=(HANDLE)-1){
  U32 n=0,header[9];DWORD written;
  while(text[n]&&n<1023)n++;
  header[0]=0x314c564e;header[1]=++sequence;header[2]=id;header[3]=(U32)before;
  header[4]=rows;header[5]=(U32)cleared;header[6]=(U32)field(engine,0xfb0a0);
  header[7]=(U32)field(engine,0xfb09c);header[8]=n;
  WriteFile(trace,header,sizeof(header),&written,0);WriteFile(trace,text,n,&written,0);
 }
 prepare(text,engine,id,history);
 show_visible_name(engine);
 if(ordinary_nvl(engine) && state_trace && state_trace!=(HANDLE)-1){
  U32 offsets[]={0xdba18,0x9680c,0x96810,0x9691c,0x96920,0x93f08c,0xf6c5c,0xf6c40,0xf6c44,0xd9f94,0xfb11c};
  U32 values[15],i,actor=read32(engine+0x93f08c);DWORD written;
  values[0]=live?sequence:(0x80000000u | (U32)((U8*)__builtin_return_address(0)-image));for(i=0;i<11;i++)values[i+1]=read32(engine+offsets[i]);
  values[12]=actor<64?read32(engine+0x9681c+actor*4):0xffffffff;
  values[13]=actor<64?read32(engine+0x9692c+actor*4):0xffffffff;
  values[14]=read32(engine+0xd9eac);
  WriteFile(state_trace,values,sizeof(values),&written,0);
  WriteFile(state_trace,engine+0xdb850,32,&written,0);
  WriteFile(state_trace,engine+0x93f00c,64,&written,0);
  WriteFile(state_trace,engine+0x93f04c,64,&written,0);
 }

}
static U8 *unique(U8 *start,U32 size,const U8 *pattern,U32 length){
 U8 *found=0;U32 i;for(i=0;i+length<=size;i++)if(equal(start+i,pattern,length)){if(found)return 0;found=start+i;}return found;
}
static U8 *make_trampoline(U8 *entry,U32 bytes){
 U8 *t=VirtualAlloc(0,bytes+5,0x3000,0x04);DWORD old;
 if(!t)return 0;copy(t,entry,bytes);t[bytes]=0xe9;
 *(U32*)(t+bytes+1)=(U32)((entry+bytes)-(t+bytes+5));
 if(!VirtualProtect(t,bytes+5,0x20,&old))return 0;
 FlushInstructionCache(GetCurrentProcess(),t,bytes+5);return t;
}
static int jump_to(U8 *entry,U32 bytes,U8 *destination){
 DWORD old;U32 i;
 if(!VirtualProtect(entry,bytes,0x40,&old))return 0;
 entry[0]=0xe9;*(U32*)(entry+1)=(U32)(destination-(entry+5));
 for(i=5;i<bytes;i++)entry[i]=0x90;
 VirtualProtect(entry,bytes,old,&old);FlushInstructionCache(GetCurrentProcess(),entry,bytes);return 1;
}
static int install(void){
 /* Relocation-free signatures, validated against the analyzed asairo.exe. */
 static const U8 call_signature[]={0x8b,0x74,0x24,0x14,0x6a,0x01,0x56,0x55,0x8b,0xcb,0xe8,0xbf,0xed,0xff,0xff,0x83,0xbd,0x9c,0xb0,0x0f,0x00,0x00};
 static const U8 opcode_signature[]={0x53,0x55,0x8b,0xac,0x24,0x74,0x24,0x00,0x00,0x56,0x57,0x8b,0xf9,0x8b,0x47,0x0c,0x8b,0x8f,0x14,0x20,0x00,0x00};
 static const U8 prep_prologue[]={0x81,0xec,0x40,0x01,0x00,0x00};
 static const U8 save_signature[]={0x8b,0x44,0x24,0x6c,0x53,0x55,0x8b,0x6c,0x24,0x70,0x56,0x57,0x33,0xff,0x68,0xf8,0x74,0x0a,0x00,0x8d,0xb5,0x00,0x77,0x89,0x00};
 static const U8 load_signature[]={0x8b,0x95,0x84,0x98,0x89,0x00,0x6a,0x01,0x52,0x55,0xe8,0x3f,0xde,0xff,0xff,0x8b,0x74,0x24,0x20};
 U8 *pe,*section,*code=0,*site,*op,*entry,*trampoline,*save_entry,*save_trampoline,*load_site;U32 size=0,n,i;DWORD old;
 image=GetModuleHandleW(0);if(!image||*(U16*)image!=0x5a4d)return 0;
 pe=image+read32(image+0x3c);if(read32(pe)!=0x4550||*(U16*)(pe+4)!=0x14c)return 0;
 n=*(U16*)(pe+6);section=pe+24+*(U16*)(pe+20);
 for(i=0;i<n;i++,section+=40)if(equal(section,(const U8*)".text",5)){code=image+read32(section+12);size=read32(section+8);break;}
 if(!code||size>0x100000)return 0;
 site=unique(code,size,call_signature,sizeof(call_signature));op=unique(code,size,opcode_signature,sizeof(opcode_signature));
 if(!site||!op)return 0;site+=10;op-=24;
 prepare=(PREP)(site+5+*(int*)(site+1));
 if(!equal((U8*)prepare,prep_prologue,6)||read32(op+1)!=0x2468||*op!=0xb8)return 0;
 /* The discovered signatures must also identify the reviewed version's RVAs. */
 if(site-image!=0x4d45c || (U8*)prepare-image!=0x4c220 || op-image!=0x4d3b0)return 0;
 message_opcode=(OPCODE)op;zero(clear_vm,sizeof(clear_vm));*(U8**)(clear_vm+0x2014)=&clear_code;
 save_entry=unique(code,size,save_signature,sizeof(save_signature));
 load_site=unique(code,size,load_signature,sizeof(load_signature));
 if(!save_entry || !load_site)return 0;save_entry-=14;
 if(save_entry-image!=0x47230 || load_site-image!=0x4e3d2 || !equal(save_entry,(const U8*)"\x83\xec\x64\xa1",4) || read32(save_entry+4)!=(U32)(image+0x761f0))return 0;
 entry=(U8*)prepare;trampoline=make_trampoline(entry,6);save_trampoline=make_trampoline(save_entry,8);
 if(!trampoline || !save_trampoline)return 0;
 prepare=(PREP)trampoline;save_snapshot=(SAVE)save_trampoline;
 if(!jump_to(entry,6,(U8*)&guarded_prepare))return 0;
 if(!jump_to(save_entry,8,(U8*)&guarded_save)){
  if(VirtualProtect(entry,6,0x40,&old)){copy(entry,trampoline,6);VirtualProtect(entry,6,old,&old);FlushInstructionCache(GetCurrentProcess(),entry,6);}
  return 0;
 }
 {char flag[2];if(GetEnvironmentVariableA("ASAIRO_NVL_TRACE",flag,2)&&flag[0]=='1'){trace=CreateFileA("nvl-trace.bin",0x40000000,1,0,2,0x80,0);state_trace=CreateFileA("nvl-state.bin",0x40000000,1,0,2,0x80,0);}}
 return 1;
}
void init(void){
 U32 i,n;WCHAR path[300];static const WCHAR tail[]={'\\','w','i','n','m','m','.','d','l','l',0};
 if(InterlockedCompareExchange(&initialized,1,0)!=0){while(initialized==1)Sleep(0);return;}
 n=GetSystemDirectoryW(path,280);if(!n||n>280)ExitProcess(101);
 for(i=0;i<11;i++)path[n+i]=tail[i];real=LoadLibraryW(path);
 if(!real||real==own)ExitProcess(102);
 for(i=0;i<EXPORT_COUNT;i++){forward[i]=GetProcAddress(real,names[i]);if(!forward[i])ExitProcess(103);}
 if(install()){static const char s[]="Native NVL active: message RVA 0x4c220, save RVA 0x47230; live pagination caller 0x4d45c; original name bytes preserved in saves.\r\n";status(s,sizeof(s)-1);}
 else {static const char s[]="NOT INSTALLED: executable/signature mismatch. WinMM forwarding remains active.\r\n";status(s,sizeof(s)-1);}
 initialized=2;
}
BOOL __stdcall DllMain(HANDLE module,DWORD reason,void*reserved){(void)reserved;if(reason==1){own=module;DisableThreadLibraryCalls(module);}return 1;}
