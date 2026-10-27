# GPL-3.0-only. Literal inverse of the locally XML-validated GHOST-only edit.
# LC_ALL=C; source XML must end in newline. Never interprets XML with regexes.
function readbytes(path,n, s,l) {
 s=""; while ((getline l < path)>0) s=s l "\n"; close(path); return substr(s,1,n)
}
function once(s,t, i) {i=index(s,t); return i && !index(substr(s,i+length(t)),t) ? i : 0}
BEGIN {old=readbytes(oldfile,oldlen);new=readbytes(newfile,newlen);body=""}
{body=body $0 "\n"}
END {
 if(oldlen>0) {p=once(body,old); if(!p) {
  if((newlen>0 && once(body,new)) || (newlen==0 && !index(body,"uid=\"47485354\""))) {printf "%s",body;exit 0}
  exit 12
 } out=substr(body,1,p-1) new substr(body,p+length(old))}
 else {if(newlen>0 && once(body,new)){printf "%s",body;exit 0};marker="</KNOWNPLUGINS>";p=once(body,marker);if(!p)exit 13;out=substr(body,1,p-1) new substr(body,p)}
 printf "%s",out
}
