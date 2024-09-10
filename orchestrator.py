import subprocess
import yaml
import time
import paramiko
import ipaddress
import sys
import os

print(chr(27) + "[2J")
print(r"""
 ______                      __       ___               _____                __                      __                   __                   
/\  _  \                  __/\ \     /\_ \             /\  __`\             /\ \                    /\ \__               /\ \__                
\ \ \L\ \    ___     ____/\_\ \ \____\//\ \      __    \ \ \/\ \  _ __   ___\ \ \___      __    ____\ \ ,_\  _ __    __  \ \ ,_\   ___   _ __  
 \ \  __ \ /' _ `\  /',__\/\ \ \ '__`\ \ \ \   /'__`\   \ \ \ \ \/\`'__\/'___\ \  _ `\  /'__`\ /',__\\ \ \/ /\`'__\/'__`\ \ \ \/  / __`\/\`'__\
  \ \ \/\ \/\ \/\ \/\__, `\ \ \ \ \L\ \ \_\ \_/\  __/    \ \ \_\ \ \ \//\ \__/\ \ \ \ \/\  __//\__, `\\ \ \_\ \ \//\ \L\.\_\ \ \_/\ \L\ \ \ \/ 
   \ \_\ \_\ \_\ \_\/\____/\ \_\ \_,__/ /\____\ \____\    \ \_____\ \_\\ \____\\ \_\ \_\ \____\/\____/ \ \__\\ \_\\ \__/.\_\\ \__\ \____/\ \_\ 
    \/_/\/_/\/_/\/_/\/___/  \/_/\/___/  \/____/\/____/     \/_____/\/_/ \/____/ \/_/\/_/\/____/\/___/   \/__/ \/_/ \/__/\/_/ \/__/\/___/  \/_/ 

""")                                                                                                                         
print("\n\n")

def check_doublon(input):
    unique = set(input)
    return len(unique) == len(input)

version_cp = input("Quelle version de CheckPoint voulez-vous installer [par exemple 81.20, notez juste le numéro]:   ")
nom_vm = input("Quel est le nom de la / des VM? (Si plusieurs, espacer les noms): ")
nom_vm = [nom.strip() for nom in nom_vm.split()]

for i in range(len(nom_vm)):
    while 'cp_mgmt' in nom_vm[i]:
        print("\n")
        nom_change = input(f"La chaine de caractères cp_mgmt ne peut pas être contenu dans le nom de la VM {nom_vm[i]}, merci de changer le nom de la VM: ")
        nom_vm[i] = nom_change
while check_doublon(nom_vm) == False:
    nom_vm = input("Il existe un doublon dans les noms, merci de les retaper correctement: ")

# version_checkpoint = input("Quelle est la version de CheckPoint à installer? [Par exemple: 81.20]  ")
choix_gw_mgmt = input("Installation d'une Gateway, Management ou SmartEvent? (espacer les paramètres si plusieurs VM) [G, M, E]:  ")
choix_gw_mgmt = [choix.strip() for choix in choix_gw_mgmt.split()]

vm_ip = input("Quelle sera l'adresse IP de la VM?:  ")
vm_ip = [ip.strip() for ip in vm_ip.split()]

for i in range(len(vm_ip)):
    while not '192.168.0.' in vm_ip[i]:
        print("\n")
        print(f"L'adresse IP de la VM {nom_vm[i]} est incorrecte")
        ip_change = input(f"Il faut obligatoirement une adresse IP dans le réseau 192.168.0.0/24, merci de retaper une adresse sous la forme 192.168.0.X: ")
        vm_ip[i] = ip_change

while not check_doublon(vm_ip):
    vm_ip = input("Il existe un doublon dans les adresses IP, merci de les retaper correctement: ")

playbook_create_vm = "create_vm_from_template.yaml"
playbook_change_shell = "change_shell.yaml"


variables_yaml = "vars.yaml"
hosts_yaml = "hosts.yaml"

MODIF_VARIABLES = 0
CREATE_VM = 0
CHANGE_SHELL = 0
CHANGE_IP = 0
IP_ADDRESS_DEFAULT_VM = "192.168.0.30"
DEFAULT_MASK = "255.255.255.0"

# Fonction pour modifier les variables dans le fichier YAML
def modifier_variables_yaml(fichier, modifications):
    global MODIF_VARIABLES
    # Lire le fichier YAML
    with open(fichier, 'r') as f:
        donnees = yaml.safe_load(f)
    
    # Appliquer les modifications
    donnees.update(modifications)
    
    # Écrire les modifications dans le fichier YAML
    with open(fichier, 'w') as f:
        yaml.safe_dump(donnees, f, default_flow_style=False)
    MODIF_VARIABLES = 1

def check_donnees(nom_vm, choix_gw_mgmt, vm_ip):
    # Affiche les données formatées.
    print("\n")
    for i in range(len(nom_vm)):
        # Assurer que toutes les listes ont la même longueur
        if i < len(choix_gw_mgmt) and i < len(vm_ip):
            print(f"nom de la VM: {nom_vm[i]}   Gateway / Management / Event: {choix_gw_mgmt[i]}    IP: {vm_ip[i]}   Masque: {DEFAULT_MASK}   Version de la VM: R{version_cp}")
            print("\n")
    verif = input("Les informations sont elles correctes? [O/N] ")
    if (verif == "O" or verif == "Oui" or verif == "oui" or verif == "o"):
        return True
    elif(verif == "N" or verif == "Non" or verif == "non" or verif == "n"):
        return False

def ping_ip(ip_address):
    """Ping l'adresse IP et retourne True si une réponse est reçue."""
    try:
        # Exécuter la commande ping LINUX
        result = subprocess.run(
            ["ping", "-c", "1", ip_address],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Vérifier si la commande ping a réussi
        return result.returncode == 0
    except Exception as e:
        print(f"Une erreur est survenue lors du ping: {e}")
        return False

def is_ip_in_network(ip, network):
    # Vérifie si une adresse IP est dans un réseau donné.
    return ipaddress.ip_address(ip) in ipaddress.ip_network(network, strict=False)

def create_vm(playbook):
    print("Création de la VM en cours...")
    global CREATE_VM
    commande = f"ansible-playbook {playbook}"
    if (MODIF_VARIABLES == 1):
        try:
            # Exécuter la commande et capturer la sortie
            result = subprocess.run(commande, shell=True, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Afficher la sortie standard
            # print("Output création de la VM :")
            # print(result.stdout)
            CREATE_VM = 1
            
            # Afficher la sortie d'erreur, s'il y en a
            if result.stderr:
                print("Sortie d'erreur :")
                print(result.stderr)
    
        except subprocess.CalledProcessError as e:
            # Gérer les erreurs spécifiques à l'exécution de la commande
            print(f"Erreur lors de l'exécution de la commande : {e}")
            print(f"Code de sortie : {e.returncode}")
            print(f"Sortie d'erreur : {e.stderr}")
        
        except Exception as e:
            # Gérer les autres exceptions
            print(f"Une erreur inattendue est survenue : {e}")

    elif (MODIF_VARIABLES == 0):
        print("Les variables n'ont pas été modifiées, les anciennes seront réutilisées!")
    print("VM déployée!")

def change_shell(playbook):
    print("Passage du Clish au Bash en cours...")
    commande = f"ansible-playbook {playbook}"
    global CHANGE_SHELL
    if (CREATE_VM == 1):
        try:
            subprocess.run(f'echo "" > $HOME/.ssh/known_hosts', shell=True, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            subprocess.run(f'ssh-keyscan {IP_ADDRESS_DEFAULT_VM} >> $HOME/.ssh/known_hosts', shell=True, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            # Exécuter la commande et capturer la sortie
            result = subprocess.run(commande, shell=True, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Afficher la sortie standard
            # print("Output changement de clish vers bash :")
            # print(result.stdout)
            CHANGE_SHELL = 1
            
            # Afficher la sortie d'erreur, s'il y en a
            if result.stderr:
                print("Sortie d'erreur :")
                print(result.stderr)
    
        except subprocess.CalledProcessError as e:
            # Gérer les erreurs spécifiques à l'exécution de la commande
            print(f"Erreur lors de l'exécution de la commande : {e}")
            print(f"Code de sortie : {e.returncode}")
            print(f"Sortie d'erreur : {e.stderr}")
        
        except Exception as e:
            # Gérer les autres exceptions
            print(f"Une erreur inattendue est survenue : {e}")

    elif (CREATE_VM == 0):
        print("La VM n'a pas été crée!")
    print("Changement du shell terminé!")

def change_ip(variables, hosts):
    global CHANGE_IP
    # Lire le fichier YAML
    with open(variables, 'r') as f:
        vars_data = yaml.safe_load(f)
    
    # Lecture du fichier Hosts
    with open(hosts, 'r') as h:
        hosts_data = yaml.safe_load(h)

# Extraire les valeurs des variables
    vm_ip = vars_data.get('vm_ip')
    # vm_net_mask = vars_data.get('vm_net_mask')
    
# Vérifier la présence de la section 'checkpoint'
    if 'checkpoint' in hosts_data and 'hosts' in hosts_data['checkpoint']:
        
        print(f"Changement de l'adresse IP en cours...")
        # Connexion à la VM et exécution des commandes
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            # Connexion SSH à adapter avec les informations d'identification
            ssh_client.connect(IP_ADDRESS_DEFAULT_VM, username='admin', password='Expert123*')

            # Exécution des commandes
            command = f"clish -c 'set interface eth0 ipv4-address {vm_ip} subnet-mask {DEFAULT_MASK}' && clish -c 'save config'"
            stdin, stdout, stderr = ssh_client.exec_command(command)
            time.sleep(3)
            ssh_client.close()
            print("Changement de l'adresse IP terminée.")
            # print(stdout.read().decode())
            # print(stderr.read().decode())
            i = 0
            while not ping_ip(vm_ip):
                i+=1
                print("La VM ne ping pas")
                if (i == 5):
                    print("[ERROR] La connexion à la VM est perdue, veuillez vous assurer que la VM Ansible soit dans le même réseau que la nouvelle IP de la VM concernée. Le script ne peux pas poursuivre.")
                    sys.exit(1)                   
                time.sleep(2)
            if ping_ip(vm_ip):
                print(f"La nouvelle IP {vm_ip} répond.")
                CHANGE_IP = 1
            else:
                print("La machine ne répond pas avec la nouvelle IP")

        except Exception as e:
            print(f"Erreur lors de la connexion ou de l'exécution des commandes : {e}")

        finally:
        # Mise à jour de l'adresse IP dans hosts.yaml
            hosts_data['checkpoint']['hosts']['check_point']['ansible_host'] = vm_ip

            # Sauvegarde des modifications dans hosts.yaml
            with open(hosts, 'w') as h:
                yaml.safe_dump(hosts_data, h, default_flow_style=False)
            print(f"L'adresse IP dans le fichier des hôtes a été mise à jour en {vm_ip}.")

    else:
        print("La section 'checkpoint' ou 'hosts' est manquante dans le fichier des hôtes.")

def gateway_mgmt_event(choix):
    if (CREATE_VM == 1):
        # Lire le fichier YAML
        with open(variables_yaml, 'r') as f:
            vars_data = yaml.safe_load(f)
        # Extraire les valeurs des variables
        vm_ip = vars_data.get('vm_ip')
        vm_name = vars_data.get('vm_name')
        vm_password = vars_data.get('vm_password')
        mgmt_admin_passwd = vars_data.get('mgmt_admin_passwd')
        mgmt_admin_name = vars_data.get('mgmt_admin_name')

        if (choix == "G" or choix == "g" or choix == "gateway"):
            ssh_ftw = f'config_system --config-string "hostname={vm_name}&ftw_sic_key={vm_password}&timezone=Europe/Paris&install_security_managment=false&install_security_gw=true&gateway_daip=false&install_ppak=true&gateway_cluster_member=false" && reboot -r now'
            try:
                print("First Time Wizard de la Gateway en cours, veuillez patienter...")
                # Exécuter la commande et capturer la sortie
                ssh_client = paramiko.SSHClient()
                ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                # Connexion SSH à adapter avec les informations d'identification
                ssh_client.connect(vm_ip, username='admin', password='Expert123*')

                # # Exécution des commandes
                stdin, stdout, stderr = ssh_client.exec_command(ssh_ftw)
                while not ping_ip(vm_ip):
                    print("First Time Wizard de la Gateway en cours, veuillez patienter...")
                    time.sleep(10)  # Attendre 10 secondes avant de réessayer

                # print(stdin, stdout, stderr)
                time.sleep(3)
                ssh_client.close()
                
            except subprocess.CalledProcessError as e:
                # Gérer les erreurs spécifiques à l'exécution de la commande
                print(f"Erreur lors de l'exécution de la commande : {e}")
                print(f"Code de sortie : {e.returncode}")
                print(f"Sortie d'erreur : {e.stderr}")
            
            except Exception as e:
                # Gérer les autres exceptions
                print(f"Une erreur inattendue est survenue : {e}")

        elif (choix == "M" or choix == "m" or choix == "management"):
            ssh_ftw = f'config_system --config-string "hostname={vm_name}&mgmt_admin_name={mgmt_admin_name}&mgmt_admin_passwd={mgmt_admin_passwd}&mgmt_gui_clients_radio=any&install_security_managment=true&install_security_gw=false&install_mgmt_primary=true&install_mgmt_secondary=false&download_info=true&upload_info=true&timezone=Europe/Paris" && reboot -r now'

            try:
                print("First Time Wizard du Management en cours, veuillez patienter...")
                # Exécuter la commande et capturer la sortie
                ssh_client = paramiko.SSHClient()
                ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                # Connexion SSH à adapter avec les informations d'identification
                ssh_client.connect(vm_ip, username='admin', password='Expert123*')

                # # Exécution des commandes
                stdin, stdout, stderr = ssh_client.exec_command(ssh_ftw)
                while not ping_ip(vm_ip):
                    print("First Time Wizard du Management en cours, veuillez patienter...")
                    time.sleep(10)  # Attendre 10 secondes avant de réessayer

                # print(stdin, stdout, stderr)
                time.sleep(3)
                ssh_client.close()

                
                while not ping_ip(vm_ip):
                    print("First Time Wizard du Management en cours, veuillez patienter...")
                    time.sleep(10)  # Attendre 10 secondes avant de réessayer

            except subprocess.CalledProcessError as e:
                # Gérer les erreurs spécifiques à l'exécution de la commande
                print(f"Erreur lors de l'exécution de la commande : {e}")
                print(f"Code de sortie : {e.returncode}")
                print(f"Sortie d'erreur : {e.stderr}")
            
            except Exception as e:
                # Gérer les autres exceptions
                print(f"Une erreur inattendue est survenue : {e}")

        elif (choix == "E" or choix == "e" or choix == "event" or choix == "smartevent"):
            ssh_ftw = f'config_system --config-string "hostname={vm_name}&ftw_sic_key={vm_password}&mgmt_admin_name={mgmt_admin_name}&mgmt_admin_passwd={mgmt_admin_passwd}&mgmt_gui_clients_radio=any&install_security_managment=true&install_security_gw=false&install_mgmt_primary=false&install_mgmt_secondary=false&download_info=true&upload_info=true&timezone=Europe/Paris" && reboot -r now'

            try:
                print("First Time Wizard du SmartEvent en cours, veuillez patienter...")

                # Exécuter la commande et capturer la sortie
                ssh_client = paramiko.SSHClient()
                ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                # Connexion SSH à adapter avec les informations d'identification
                ssh_client.connect(vm_ip, username='admin', password='Expert123*')

                # # Exécution des commandes
                stdin, stdout, stderr = ssh_client.exec_command(ssh_ftw)
                while not ping_ip(vm_ip):
                    print("First Time Wizard du SmartEvent en cours, veuillez patienter...")
                    time.sleep(10)  # Attendre 10 secondes avant de réessayer

                # print(stdin, stdout, stderr)
                time.sleep(3)
                ssh_client.close()
                
                while not ping_ip(vm_ip):
                    print("First Time Wizard du SmartEvent en cours, veuillez patienter...")
                    time.sleep(10)  # Attendre 10 secondes avant de réessayer
                        
            except subprocess.CalledProcessError as e:
                # Gérer les erreurs spécifiques à l'exécution de la commande
                print(f"Erreur lors de l'exécution de la commande : {e}")
                print(f"Code de sortie : {e.returncode}")
                print(f"Sortie d'erreur : {e.stderr}")
            
            except Exception as e:
                # Gérer les autres exceptions
                print(f"Une erreur inattendue est survenue : {e}")


    elif (CREATE_VM == 0):
        print("La VM n'existe pas!")
    else:
        print("Un problème est survenu dans la fonction create_vm, merci de vérifier la valeur finale de la variable CREATE_VM")
    while not ping_ip(vm_ip):
        print(f"La VM est en cours de redémarrage, veuillez patienter...")
    print("La VM est prête!")
    
def host_reset(hosts):
        # Lecture du fichier Hosts
    try:
        with open(hosts, 'r') as h:
            hosts_data = yaml.safe_load(h)

        while (hosts_data['checkpoint']['hosts']['check_point']['ansible_host'] != IP_ADDRESS_DEFAULT_VM):
            hosts_data['checkpoint']['hosts']['check_point']['ansible_host'] = IP_ADDRESS_DEFAULT_VM
        
            # Sauvegarde des modifications dans hosts.yaml
        with open(hosts, 'w') as h:
            yaml.safe_dump(hosts_data, h, default_flow_style=False)
    except:
        print("Le fichier hosts n'a pas pu être réinitialisé, pensez à changer manuellement les adresses IP pour qu'Ansible puisse avoir accès aux futures VM.")
        return False
    return True
    
def main():

    host_reset(hosts_yaml)

    if (check_donnees(nom_vm, choix_gw_mgmt, vm_ip)):

        for i in range(len(nom_vm)):
            # Appliquer les modifications
            modifications = {
                'vm_ip': vm_ip[i],
                'vm_name': nom_vm[i],
                'vm_template': f'CheckPoint-R{version_cp}',
            }

            modifier_variables_yaml(variables_yaml, modifications)
            create_vm(playbook_create_vm)

            while not ping_ip(IP_ADDRESS_DEFAULT_VM):
                print("La VM est en cours de démarrage, veuillez patienter...")
                time.sleep(10)  # Attendre 10 secondes avant de réessayer

            time.sleep(10)
            # Lorsque le ping réussit, appeler la fonction suivante
            change_shell(playbook_change_shell)

            while not ping_ip(IP_ADDRESS_DEFAULT_VM):
                print("La VM est en cours d'initialisation, veuillez patienter...")
                time.sleep(10)  # Attendre 10 secondes avant de réessayer

            change_ip(variables_yaml, hosts_yaml)

            gateway_mgmt_event(choix_gw_mgmt[i])

            
            host_reset(hosts_yaml)
    else:
        print("Merci de relancer le script en entrant les bonnes informations.")



# Exécuter le script
if __name__ == "__main__":
    main()
