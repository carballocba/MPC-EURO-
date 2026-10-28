# Strict XML subset used by MPC.settings; no DTD/entities beyond XML built-ins.
# report=registry emits canonical PLUGIN attributes; report=locations emits Location text.
function bad(){err=1;exit 1}
function entities(s, t){t=s;gsub(/&amp;|&lt;|&gt;|&quot;|&apos;|&#[0-9]+;|&#x[0-9a-fA-F]+;/,"",t);return index(t,"&")==0}
function decode(s){gsub(/&lt;/,"<",s);gsub(/&gt;/,">",s);gsub(/&quot;/,"\"",s);gsub(/&apos;/,"'",s);gsub(/&amp;/,"\&",s);return s}
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
 if(closing){if(t!=name || depth<1 || stack[depth]!=name)bad();if(name=="Location"&&incontent&&report=="locations")print decode(text);if(name=="SynthContentLocations")incontent=0;depth--;return}
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
