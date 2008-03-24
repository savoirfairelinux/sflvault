How to use SFLvault
===================

Client's naming conventions:

 c#123 - Customer ID
 m#521 - Machine ID (server id)
 s#768 - Service ID
 u#52  - User ID


Example usage:

-------------------
[auth-required]
$ sflvault ssh s#235
Drops you, 2 hops over on the right server, sending passwords when required.
-------------------

-------------------------
[auth-required]
$ sflvault search reg1 exps2.*
Show a list of servers/services that match, without any secrecy passed on.

[auth-required]
$ sflvault show s#123
Shows a nice map of the services you need to reach, to get there, in a hierarchy,
decrypting the passwords you have access to.

[nothing-required]
$ sflvault alias enzyme01 s#566
Adds an internal alias (saved in the config .ini file), whenever a service
is requierd, you can just put there the alias.

[nothing-required]
$ sflvault unalias enzyme01
Removes the alias

[nothing-required]
$ sflvault alias
Lists all the aliases
-------------------------




----------------------------------------------
[admin-only, auth-required]
$ sflvault adduser username
Creates a new spot for the new "username" to setup, this request lasts 15 seconds,
after than, the new "username" spot gets freed.

[new-user]
$ sflvault setup username https://vault.address:port/path
Creates a new key-pair, and sends it into the vault.
Saves the private-key, and encrypted it on the disk with a passphrase.
Stores also the URL of the vault, and the user's username.
Sets to NULL the `waiting_setup` field.
If server refuses, remove all stored keys, username and url local data.
If NO user exists on the server-side (fresh new install)

### Mieux si le serveur génère un secret qui va permettre au gars d'activer son
### accompte.

[admin-only, auth-required]
$ sflvault grant username level1,level2,level3
Re-encrypts the symkeys for 'level1', 'level2' and 'level3' with the pub-key
of the user `username`, stores it in the userciphers table.

[admin-only, auth-required]
$ sflvault revoke username [--all|level1,level2,level3]

[admin-only, auth-required]
$ sflvault list-users
Lists all users

[auth-required]
$ sflvault list-levels
Shows all access levels

[admin-only, auth-required]
$ sflvault deluser username
Removes the user `username` and removes ALL encrypted symkeys
associated with that user. Remove also the public-key info for
this user. This renders the private-key for that user (even on
it's computer), completely useless.
----------------------------------------------

# If user lost his private key, password, etc, to reset a user
# issue `deluser` then `adduser`, `setup` and `grant` again.



# To add some info into the vault
----------------------------------------------
[auth-required]
$ sflvault addcustomer --name|-n "customer name"
Prints the customer number.

[auth-required]
$ sflvault list-customers
Lists all customers, in $PAGER with their numbers.

[auth-required]
$ sflvault addserver --name|-n "server name" --fqdn|-d "domain name"
                     --ip|-i "ip address" --location|-l "location"
Offers a list of customers, with $PAGER, you can select the number from a list,
and fills the info with that.

[auth-required]
$ sflvault addservice --type|-t "service type" --port|-p portnum
                      --login|--loginname|-l "root et al" --level "level"
		      --notes "these are some notes\nand you can add more and more."
You'll be prompted to enter the new secret (or password).
If level doesn't exist (in xmlrpc: list-levels), show them, and ask to confirm
  creation of a new level.
----------------------------------------------




Private key and config will be stored in ~/.sflvault, with enforced permissions
of 0700 for the dir. and 0600 for every file in there (like openssh).
~/.sflvault/config (simple .ini file, with username, and vault url)
~/.sflvault/key    (encrypted ElGamal private key, for authentication and decryption of cryptograms)



------------------------------------------
XML-RPC interface:

login username
  `- return a ciphertext to be decrypted and returned to the server using that user's
     private key.
authenticate username plaintext
  `- returns the 'authtok', and 'session_timeout' required for subsequent calls
list-customers authtok
  `- returns a simple list of customers with their customer_id
add-customer authtok, customer_name
list-servers authtok
  `- returns a simple list of servers (with their customer info)
list-levels authtok
  `- returns a very simple list of existing levels.
     simple GROUP BY 'level' on userlevels.
list-users authtok
  `- returns a simple list of the users (with pub keys?), and their levels
search authtok keywords
  `- returns a list of servers/services in a hierarchy that match the criterias (searches in all fields)
show authtok service_id
  `- returns a list of servers/services with crypto data along the reply, ready to be decrypted by the
     authenticated user
adduser authtok username
  `- requires admin privs, prepares the users with waiting_setup stamp. 15 seconds timeout allowed.
setup username pubkey
  `- does NOT require authentication. Stores the public key, and resets the waiting_setup field.
     Stamps the created_time. At each of those requests, the server clears the from the users table
     all expired non NULL waiting_setup lines. Those should not have any stuff added
grant authtok username [level1, level2, level3]
 `- starts a round-cycle of encryption of the symkeys for those levels
logout
 `- destroys the authtok, and destroys session on server's side.


----------------------------------------------------
Crypto schemas:

client's private keys encrypted locally with Blowfish, with a symkey of
variable length. Users are encouraged to use secure and long keys.


All 'secret' of the `services` table are encrypted using randomly chosen
32 bytes AES256 symkeys, this key is then encrypted with the public ElGamal
key for each user part of that service's level.

All Userciphers are (AES256) 32 bytes symkeys encrypted with the ElGamal
public-key of that particular user.

ElGamal(1536 bits, with random K values)


elgamal message:
  serial_elgamal_msg / unserial_elgamal_msg, voir lib/base.py

elgamal pubkey:
  serial_elgamal_pubkey / unserial_elgamal_pubkey, même chose que *_elgamal_msg, voir lib/base.py

elgamal privkey:
  

keys/stuff marshalling/unmarshalling:
  e = clé ElGamal générée.
  pubkey = b64encode(simplejson.dumps((e.p, e.g, e.y)))
  privkey = b64encode(simplejson.dumps((e.p, e.x)))

pubkey est shippé direct comme ça dans la BD
privkey est encrypté (à partir de la) en Blowfish, et écrit direct sur le
  disque dans ~/.sflvault/config  avec les modes changés et renforcés.

pour décoder les pubkey:
  e = new ElGamalObj()
  (e.p, e.g, e.y) = simplejson.loads(b64decode(pubkey))

pour décoder la privkey:
  (p, x) = simplejson.loads(b64decode(privkey))

----------------------------------------------------
Authentication scheme:

client issues xmlrpc:login(username)
server returns some randombytes, encrypted with the username's pubkey
client issues xmlrpc:authentication(username, decrypted_randombytes)
server returns the authtok (required for subsequent authenticated calls)
               and a session timeout (from vault's configuration)

client issues xmlrpc:list-customerss(authtok)
server checks the authtok, updates the timeout, and returns the list.



----------------------------------------------------
Basic implementation details to take into consideration:

A user is NOT a user until waiting_setup IS NOT NULL.



----------------------------------------------------
Server-side configuration, on install:

[authentication]
sessions_timeout=300   # Seconds for session timeout
                       # when the user must re-issue
                       # a login() and authenticate()
  
