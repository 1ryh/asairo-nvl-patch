"""Generate native overrides from the user-owned archive without writing game files."""
import struct
if __package__:
    from .mpk import entries
    from .panel import rounded_panel
else:
    from mpk import entries
    from panel import rounded_panel

def generate(game):
    changes=[]
    def arg(value,kind=0):return bytes([kind])+struct.pack('<i',value)
    def once(data,old,new,label):
     assert len(old)==len(new),(label,'size changed')
     assert data.count(old)==1,(label,'signature count',data.count(old))
     changes.append(dict(label=label,file_offset=hex(data.index(old)),before=old.hex(),after=new.hex()))
     return data.replace(old,new)
    scripts={n.lower():b for n,_,_,b in entries(game/'Scenario.mpk')}
    source=scripts['01gamenov.msc'];data=source
    obj=arg(1000,1)
    data=once(data,b'\x05\x01'+obj+arg(58)+arg(10),b'\x05\x01'+obj+arg(80)+arg(58),'native message text origin')
    data=once(data,b'\x01\x0a'+arg(26)+arg(16),b'\x01\x0a'+arg(25)+arg(13),'native wrap columns and page rows')
    data=once(data,b'BG\\IM00.mgr',b'BG\\NV00.mgr','native message object background resource')
    data=once(data,b'\x02\x0e'+obj+arg(50),b'\x02\x0e'+obj+arg(100),'native background opacity')
    data=once(data,b'\x02\x01'+obj+arg(0)+arg(0),b'\x02\x01'+obj+arg(56)+arg(36),'native background origin')
    # Native transparency setting (01 1c, selector 14, two typed integers).
    # Prepend to code and relocate both native 9-byte label tables. Label offsets
    # are code-relative, confirmed in LoadMSC at VA 00457e10.
    code_start=struct.unpack_from('<I',data,2)[0]
    setting=b'\x01\x1c\x14'+arg(0)+arg(45)
    header=bytearray(data[:code_start]);table=10
    for _ in range(2):
     length=struct.unpack_from('<I',header,table-4)[0]
     assert length%9==0
     for at in range(table,table+length,9):
      offset=struct.unpack_from('<I',header,at+5)[0]
      assert offset<len(data)-code_start
      struct.pack_into('<I',header,at+5,offset+len(setting))
     table+=length+4
    assert table-4==code_start
    changes.append(dict(label='native transparency 45 percent, measured from Itsusora; relocate label offsets',file_offset=hex(code_start),inserted=setting.hex()))
    data=bytes(header)+setting+data[code_start:]
    # Native BGRA panel: per-pixel corner alpha plus native 45% transparency.
    mgr=rounded_panel()
    for variant in ['hiy','oth','nak']:
     old=scripts[f'01game_{variant}.msc'];normalized=old
     for asset in ['01mess','01mess_fr','01name','01name_fr']:
      resource=f'System\\{asset}_{variant.upper()}.mgr'.encode('ascii')
      simple=f'System\\{asset}.mgr'.encode('ascii')
      signature=struct.pack('<I',len(resource))+resource
      assert normalized.count(signature)==1
      normalized=normalized.replace(signature,struct.pack('<I',len(simple))+simple)
     code_start_old=struct.unpack_from('<I',old,2)[0]
     code_start_adv=struct.unpack_from('<I',scripts['01game.msc'],2)[0]
     assert normalized[code_start_old:]==scripts['01game.msc'][code_start_adv:]
    files={f'Scenario/{name}.msc':data for name in ['01game','01game_HIY','01game_OTH','01game_NAK']}
    files['BG/NV00.mgr']=mgr
    return files, changes
