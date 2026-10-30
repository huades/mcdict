import pathlib,struct,re

ROOT=pathlib.Path(__file__).resolve().parents[1]
def extract():
    data=next(ROOT.parent.glob('*.mobi')).read_bytes()
    count=struct.unpack_from('>H',data,76)[0]
    offsets=[struct.unpack_from('>I',data,78+i*8)[0] for i in range(count)]+[len(data)]
    records=[data[offsets[i]:offsets[i+1]] for i in range(count)]
    header=records[0]
    compression,_,length,ntext,_,encryption=struct.unpack_from('>HHIHHI',header)
    assert compression==2 and encryption==0
    flags=struct.unpack_from('>H',header,242)[0]
    def decompress(src):
        src=bytearray(src)
        for bit in range(1,16):
            if flags & (1<<bit):
                size=0; shift=0
                for b in reversed(src):
                    size|=(b&127)<<shift; shift+=7
                    if b&128: break
                del src[-size:]
        if flags&1: del src[-((src[-1]&3)+1):]
        out=bytearray(); i=0
        while i<len(src):
            b=src[i];i+=1
            if 1<=b<=8: out.extend(src[i:i+b]);i+=b
            elif b<128: out.append(b)
            elif b>=192: out.extend((32,b^128))
            else:
                pair=(b<<8)|src[i];i+=1
                distance=(pair&0x3fff)>>3; size=(pair&7)+3
                if not distance: raise ValueError('Invalid PalmDOC distance')
                for _ in range(size): out.append(out[-distance])
        return out
    raw=b''.join(decompress(r) for r in records[1:ntext+1])[:length]
    raw.decode('utf-8',errors='strict')
    return raw,records,struct.unpack_from('>I',header,108)[0]

if __name__=='__main__':
    raw,_,_=extract()
    print(len(raw)); print(raw[:4500].decode('utf-8'))
    decoded=raw.decode('utf-8',errors='strict');marker=decoded.find('安静');print(decoded[max(0,marker-100):marker+1100])
