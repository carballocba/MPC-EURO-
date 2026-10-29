# Strict XML subset used by MPC.settings; no DTD/entities beyond XML built-ins.
# report=registry emits canonical PLUGIN attributes; report=locations emits Location text.
function bad(){err=1;exit 1}
# Decode once, in document order. Never reinterpret an ampersand produced by an entity.
# Byte-oriented UTF-8 output works with BusyBox/POSIX awk under LC_ALL=C.
function utf8(n){
 if(n<128)return sprintf("%c",n)
 if(n<2048)return sprintf("%c%c",192+int(n/64),128+n%64)
 if(n<65536)return sprintf("%c%c%c",224+int(n/4096),128+int(n/64)%64,128+n%64)
 return sprintf("%c%c%c%c",240+int(n/262144),128+int(n/4096)%64,128+int(n/64)%64,128+n%64)
}
function decode(s, out,p,e,n,i,d,base,c){
 out=""
 while((p=index(s,"&"))){
  out=out substr(s,1,p-1);s=substr(s,p+1);p=index(s,";");if(!p)bad()
  e=substr(s,1,p-1);s=substr(s,p+1)
  if(e=="amp")c="&"
  else if(e=="lt")c="<"
  else if(e=="gt")c=">"
  else if(e=="quot")c="\""
  else if(e=="apos")c="'"
  else {
   base=10
   if(e~/^#x[0-9a-fA-F]+$/){base=16;e=substr(e,3)}
   else if(e~/^#[0-9]+$/)e=substr(e,2)
   else bad()
   n=0
   for(i=1;i<=length(e);i++){
    d=index("0123456789abcdef",tolower(substr(e,i,1)))-1
    n=n*base+d;if(n>1114111)bad()
   }
   # XML 1.0 Char production: no NUL, surrogates or FFFE/FFFF.
   if(!(n==9||n==10||n==13||(n>=32&&n<=55295)||(n>=57344&&n<=65533)||(n>=65536&&n<=1114111)))bad()
   c=utf8(n)
  }
  out=out c
 }
 return out s
}
function entities(s, ignored){ignored=decode(s);return 1}
function emit( k,i,j,tmp,n){
 n=0;for(k in attrs)keys[++n]=k
 for(i=1;i<=n;i++)for(j=i+1;j<=n;j++)if(keys[j]<keys[i]){tmp=keys[i];keys[i]=keys[j];keys[j]=tmp}
 tmp="PLUGIN";for(i=1;i<=n;i++){k=keys[i];tmp=tmp" "k"=\""attrs[k]"\"";delete keys[i]}
 if(report=="registry") print tmp
 if(report=="ghost" && attrs["uid"]=="47485354") print "<"tmp" />"
}
function tag(t, closing,self,name,a,k,q,v,pos){
 if(t~/^<\?xml /){if(root || depth)bad();return}
 if(t~/^<!/)bad()
 closing=(t~/^<\//);self=(t~/\/>$/);sub(/^<\/?/,"",t);sub(/\/?[>]$/,"",t);sub(/[ \t\r\n]+$/,"",t)
 name=t;sub(/[ \t\r\n].*$/,"",name);if(name!~/^[A-Za-z_][A-Za-z0-9_.:-]*$/)bad()
 if(closing){if(t!=name || depth<1 || stack[depth]!=name)bad();if(name=="Location"&&incontent&&report=="locations"){decoded=decode(text);if(decoded~/[[:cntrl:]]/)bad();print decoded;}if(name=="SynthContentLocations")incontent=0;depth--;return}
 a=substr(t,length(name)+1);for(k in attrs)delete attrs[k]
 while(a!=""){
  if(a!~/^[ \t\r\n]+/)bad();sub(/^[ \t\r\n]+/,"",a);if(a=="")break
  k=a;sub(/[= \t\r\n].*$/,"",k);if(k!~/^[A-Za-z_][A-Za-z0-9_.:-]*$/ || k in attrs)bad();a=substr(a,length(k)+1);sub(/^[ \t\r\n]*/,"",a);if(substr(a,1,1)!="=")bad();a=substr(a,2);sub(/^[ \t\r\n]*/,"",a)
  q=substr(a,1,1);if(q!="\""&&q!="'")bad();a=substr(a,2);pos=index(a,q);if(!pos)bad();v=substr(a,1,pos-1);if(index(v,"<")||!entities(v))bad();attrs[k]=v;a=substr(a,pos+1)
 }
 if(depth==0){if(root++ || name!="PROPERTIES")bad()}
 if(name=="PLUGIN"){if(!self || !("uid" in attrs) || !("file" in attrs))bad();emit()}
 if(name=="SynthContentLocations")incontent=1
 if(name=="Location"){if(!incontent || self)bad();text=""}
 if(!self)stack[++depth]=name
}
{ doc=doc $0 "\n" }
END{
 if(err)exit 1
 while(length(doc)){
  p=index(doc,"<");if(!p){if(doc!~/^[ \t\r\n]*$/)bad();break}
  raw=substr(doc,1,p-1);if(!entities(raw))bad();if(depth==0 && raw!~/^[ \t\r\n]*$/)bad();if(stack[depth]=="Location")text=text raw
  doc=substr(doc,p)
  # Find > only outside quotes, permitting escaped XML in preference attributes.
  quote="";end=0
  for(j=2;j<=length(doc);j++){ch=substr(doc,j,1);if(quote!=""){if(ch==quote)quote=""}else if(ch=="\""||ch=="'")quote=ch;else if(ch==">"){end=j;break}}
  if(!end)bad();token=substr(doc,1,end);doc=substr(doc,end+1);tag(token)
 }
 if(depth!=0 || root!=1)exit 1
}
