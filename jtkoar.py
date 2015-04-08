#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
import getopt
import sqlite3 as sql
import time
import getpass

# Programme servant d'intermédiaire en utilisateur du mini-datacenter et le data cente


# Variables globales et paramètres systèmes
database_name='/var/cache/jtkoar/jtkoar.db'			# Chemin de la base données de jtkoar
nfsserver_adresseip="192.168.137.130"				# Adresse ip du serveur NFS
nfsserver_port="2049"								# Port d'écoute du serveur NFS

# Procédure d'analyse des arguments de la ligne de commande
def usage():
	print "===========================================================================" 
	print "" 
	print "	Usage: jtkoar -vabhds [-u user] [-i image] [-c cardid]" 
	print "		-h: affiche l'aide courante" 
	print "		-a: ajout d'un user, d'une image ou d'une carte" 
	print "		-b: connexion d'un user à une session jtkoar préalablement" 
	print "		-d: démarrer une carte disponible quelconque avec l'image" 
	print "		-s: supprimer d'un user, d'une image ou d'une carte" 
	print "" 
	print "===========================================================================" 

def simulscroll(wait_interval, repeat_number):
	for i in range(1,repeat_number):
		print ".",  
		sys.stdout.flush()
		time.sleep (wait_interval)	
	print "."
	sys.stdout.flush()
	time.sleep (wait_interval)	
	

# Procédure d'analyse des arguments de la ligne de commande
def main(argv):
	grammar = "kant.xml"
	try:
		opts, args = getopt.getopt(argv, "vabdhsi:u:c:n:k:", ["help", "grammar="])
	except getopt.GetoptError:
		usage()
		sys.exit(2)
		
	for opt, arg in opts:
		if opt=='-i':
			newimage_name=arg
		if opt=='-c':
			carte_name = arg		
		else:
			carte_name = "Carte1"
		if opt=='-u':
			user_name = arg
		if opt=='-n':
			carte_nfsroot = arg

	for opt, arg in opts:
		if opt in ("-h", "--help"):
			usage()
			sys.exit()
		elif opt=='-d':
			start_session(carte_name,newimage_name)
		elif opt=='-b':     
			bind_session(carte_name)
		elif opt=='-a':
			print("Ajout d'une carte, d'un user, d'une image xxxx")
		elif opt=='-s':
			print("Démarrage de l'image xxxx sur une des cartes disponible")            
		elif opt=='-h':
			usage()
			sys.exit(0)

def start_session(carte_name, newimage_name):
	print "========== DEMARRAGE IMAGE OS SUR UNE CARTE JTK DISPONIBLE ================"	
	print "1. Allocation d'une carte",
	simulscroll(500.0 / 1000.0, 4)
	print "	- Carte allouée : %s " % carte_name 	
	print "	- Image demandée : %s " % newimage_name

	con=None
	try:
		## Connexion à la base de donnée SQLITE3
		con=sql.connect(database_name)

		# Charger les détails sur la carte et sur l'image actuellement configuré pour booter la carte sélectionné	    	
		cur=con.cursor()
		cur.execute("SELECT name,nfsroot,image_name, image_owner, image_ipadress FROM JTKCARD WHERE name=:cname",{"cname": carte_name})
		row=cur.fetchone()        

		if row!=None:
			carte_nfsroot=row[1]
			oldimage_name=row[2]
			oldimage_owner=row[3]
			oldimage_adresseip=row[4]

			newimage_owner=getpass.getuser()
			
			if oldimage_name!=newimage_name or oldimage_owner!=newimage_owner :	
				# Charger les détails sur l'image sélectionné par l'utilisateur
				cur=con.cursor()
				cur.execute("SELECT owner, ipadress FROM JTKIMAGE WHERE name=:iname and owner=:iowner",{"iname": newimage_name,"iowner": newimage_owner})
				row=cur.fetchone()

				if row!=None:
					newimage_owner=row[0]
					newimage_adresseip=row[1]

					## Initiation du redémarrage de la carte 
					print "2. Redémarrage de la carte %s " % carte_name					
					os.system("ssh -i /var/cache/jtkoar/id_rsa  root@%s reboot " % oldimage_adresseip)
					
					## Attendre la termination de la connexion NFS au partage
					print "	- Attente du fermeture de la session NFS du partage %s jadis exploite par la carte %s " % (carte_nfsroot, carte_name)
					nbcur=0
					while True :
						nbrcon=os.system("netstat -an | grep %s:%s > /dev/null 2>&1 " % (nfsserver_adresseip,nfsserver_port))  #/dev/null 2>&1
						nbcur=nbcur+1
						print ".",						
						sys.stdout.flush() 
						if (nbrcon==256 and nbcur>=20) :
							print "."
							break
						time.sleep (500.0 / 1000.0)
					
					print "	- Desactivation du partage %s jadis exploite par la carte %s " % (carte_nfsroot, carte_name)		
					os.system("exportfs -u *:%s" % carte_nfsroot)
					
					print "	- Sauvegarde de l'image actuellement reference par %s dans /home/%s/NFSRoots/%s" % (carte_nfsroot,oldimage_owner,oldimage_name)
					os.system("chown %s:%s %s" % (oldimage_owner, oldimage_owner , carte_nfsroot)) 	
					os.system("mv %s /home/%s/NFSRoots/%s" % (carte_nfsroot , oldimage_owner , oldimage_name))
					
					print "	- Redirection de l'image /home/%s/NFSRoots/%s vers le partage %s " % (newimage_owner,newimage_name,carte_nfsroot)
					os.system("mv /home/%s/NFSRoots/%s %s" % (newimage_owner,newimage_name,carte_nfsroot))		
					os.system("chown root:root %s" % carte_nfsroot)
					
					print "	- Reactivation du partage NFS %s " % carte_nfsroot
					os.system("exportfs -o rw,nohide,insecure,no_subtree_check,async,no_root_squash *:%s" % carte_nfsroot)			

					print "	- Attente du demarrage de la carte %s" % carte_name
					nbcur=0
					while True :
						nbrcon = os.system("netstat -an | grep %s:%s > /dev/null 2>&1" % (nfsserver_adresseip,nfsserver_port))  
						print ".",
						sys.stdout.flush() 
						nbcur=nbcur+1
						if (nbrcon!=256 or nbcur>=30) :
							print "."
							break
						time.sleep (1.5)
					# Enregistrement de la session Carte - Image OS dans la base de données de jtkoar.
					print "	- Enregistrement de la session Carte - Image OS dans la base de donnees de jtkoar."
					cur=con.cursor()
					cur.execute("UPDATE JTKCARD SET image_name=:iname,image_owner=:iowner,image_ipadress=:iipadress where name=:cname",{"iname": newimage_name, "iowner": newimage_owner,"iipadress": newimage_adresseip,"cname": carte_name})
					con.commit()	
					
					print "3. Ouverture et transfert session ssh utilisateur sur la carte %s " % carte_name
					os.system("ssh %s" % newimage_adresseip)					
				else:
					print "	- L'image spêcifié n'existe pas !" 	
			else:
				print "	- L'image demandé est déjà encours d'execution sur la carte %s "  % carte_name
		else:
		    print "	- Aucune carte disponible pour booter cette image ou carte sélectionné non existente"

		## Déconnexion de la base de donnée
		con.close()
		con=None
	except sql.Error, e:	  
		print "Erreur d'accès à la base de donnée %s:" % e.args[0]
		sys.exit(1)	    
	finally:    
		if con:
			con.close()
	

def bind_session(cart_name):
	print "========== OUVERTURE/CONNEXION SESSION OS SUR UNE CARTE JTK  ================"	
	print " Carte concernée : %s " % cart_name 
	time.sleep (500.0 / 1000.0)	


if __name__ == "__main__":
	main(sys.argv[1:])	

# Affichage de l'aide 
#def afficher_aide
