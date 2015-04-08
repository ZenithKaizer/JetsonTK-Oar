.open /var/cache/jtkoar/jtkoar.db

create table jtkuser (user_name text not null);
create table jtkcard (name text not null, nfsroot text not null, image_name text, image_owner text, image_ipadress);
create table jtkimage (name text not null, owner text not null, ipadress text not null);

Insert into JtkImage Values ('Carte1','/NFSRoot1','jtkuser1','192.168.78.131');


Insert into JtkImage Values ('RootFS1','jtkuser1','192.168.78.131');
Insert into JtkImage Values ('RootFS2','jtkuser1','192.168.78.131');
Insert into JtkImage Values ('RootFS1','jtkuser2','192.168.78.131');
.quit
