
Permissions and cryptographic constraints
=========================================

This page lists all the permissions you have, and by which means you have
them.  If it is protected by the Vault server (allowing or disallowing
certain things), or if it is protected by cryptographic means (mathematically
can't be accessed, unless certain passwords, passphrases, keys are provided).

We'll start with a bullet-pointed list of all the constraints, and we'll
try to make it a table or a graph and order all of this sooner or later:

* user-setup must be called before 300 seconds (can be configured in .ini file under "sflvault.vault.setup_timeout")
* user-add will fail if user exists
* user-add requires 'global-admin' via xml-rpc. Direct library allowed.
* user-add will update the setup time if it was timed out. Same restrictions apply.
* user-del requires 'global-admin' via xml-rpc. Direct library access allowed.  Will remove user directly if it exists.
* user-list requires authentication via xml-rpc.  Direct lib. access allowed.  Lib returns setup status, if user is admin, and it's groups (include admin membership of groups).
* service-get requires authentication via xml-rpc.  Direct lib access allowed.  Returns the service.
* service-put requires authentication via xml-rpc.  Direct lib access allowed.  WARNING: No groups constraints are applied, to update service. TODO: apply these checks in XML-RPC.
* show (service-get-tree in lib) requires auth. via xml-rpc.  Direct lib access allowed.
* search requires authentication via xml-rpc.  Direct lib access allowed.  Returns search results.
* customer_get requires authentication via xml-rpc.  Direct lib access allowed. 
* customer_put requires authentication via xml-rpc.  Direct lib access allowed. 
* customer_add requires authentication via xml-rpc.  Direct lib access allowed. 
* customer_del requires 'global-admin' permissions via xml-rpc.  Direct lib access allowed.  Deleting a customer deletes all it's machines and services.
* machine_put requires authentication via xml-rpc.  Direct lib access allowed.  Anyone can update machine infos.
* machine_get requires authentication via xml-rpc.  Direct lib access allowed.
* machine_add requires authentication via xml-rpc.  Direct lib access allowed.
* service_add requires authentication via xml-rpc.  Direct lib access allowed.  No group restrictions applied.  Every user can add a service to any group.  Doesn't mean he's going to be able to read it.
* group_get requires auth via xml-rpc.  Direct lib access allowed.
* group_put requires auth via xml-rpc.  Direct lib access allowed.  Group admin required to 'hide' group.  Constraint applied in the library (not at XML-RPC level). TODO: change this behavior, make the checks in XML-RPC lib.
* group_add requires auth via xml-rpc.  Direct lib access allowed.  Requires self.myself_id to add a group.  Anyone can add a group.  The one adding a group becomes admin of this group.  Any service then added to this group will be accessible to the members of that group.
* group_del requires 'global-admin' via xml-rpc.  Direct access to lib allowed.  Library doesn't allow deletion of non-empty groups.
* group_list requires auth via xml-rpc.  Direct access to lib allowed.  Doesn't show hidden groups to non-members of those groups, except for global admins.  Via xml-rpc, can't override behavior.  Direct lib access allows override (see all groups no matter which hidden status it is in, with show_hidden=True).  TODO: make sure this is true! 
* group_add_service requires auth via xml-rpc.  Direct lib allowed.  CRYPTO constraint: you need to have a decrypted service symkey (requiring your private key, and previous access to service_get) to add a service to any group.  The vault has no means to verify the consistency of your symkey.  Providing random symkeys will create an unusable service (accessed via this group).

* group_del_service requires simple auth via xml-rpc.  Direct lib allowed.  Lib constraint: service must be in another group to be detached from this group (otherwise you'd lose your service :).  XML-RPC constraint: can't delete group if you're not admin of the group nor global-admin.  TODO: move group constraints and admin constraints to XML-RPC layer.

* group_add_user requires XML-RPC auth.  Lib access allowed. CRYPTO constraint: you need to have a decrypted group key (requiring your private key, and previous access to group_add_user to retrieve the user's public key, and the group's encrypted private key).  Lib enforces being in the group, since this is the only way you can provide a validly encrypted groupkey.  Being global-admin in any case doesn't help here (because of CRYPTO constraints).  This command trusts that the remote user adding another user enters valid data as a cryptgroupkey. If junk is added in that field, the added user simply won't be able to access the group's data. Also will he need to be removed and added successfully to the group for everything to work.  TODO: implement group's symkey encryption + migration scripts.
* group_del_user requires simple auth via XML-RPC.  Lib access allowed.  Lib constraints prevents from deleting yourself from the group.  Makes sure someone else will remain in the group.  The library will make everything possible to make sure there is at least a group admin left.  It will warn if there is no more.  It will prevent you from deleting the last admin.  XML-RPC will block if you are not either group-admin of this group, or global-admin.  TODO: Admin flags are to be verified in the XML-RPC layer.
* machine_del requires 'global-admin' via xml-rpc.  Lib access is allowed.  Lib constraint: prevent deleting a machine that containts a service that is a parent to another service.  Otherwise, delete machine and it's services.
* service_del requires 'global-admin' via xml-rpc.  Lib access is allowed.  Lib constraint: won't remove a service with childs.  If user is global admin, allow.  If user is admin of all groups the service is in, allow.  Otherwise, you'll have to ask each admins of each groups the service is in to detach the service first.  TODO: move admin checks to XML-RPC, require auth and more checks in body.  DOUBLE CHECK
* customer_list requires auth via xml-rpc.  Lib access allowed.  No constraints.
* machine_list requires auth via xml-rpc.  Lib access allowed.  No constraints.
* service_list requires auth via xml-rpc.  Lib access allowed.  No constraints.  NO cryptogram is sent with responses to `service_list`.
* service_passwd requires auth via xml-rpc.  Lib access allowed.  Constraints: lib (and xml-rpc call) refuses to perform operation if you don't have access to decrypt the password first.  The call to this function will not actually decrypt anything, it will just make sure you're not overwriting some data you didn't previously have access to.


TODO: documenter ce qui est cryptographié, et ce qui est accessible si la voute est compromise.

TODO: note functions that requires self.myself_id to operate.


NOTE: first user called admin, implication, where to store it's credentials.  Use it as a user, or not ?  Ça en prendra un.  Procédure sera d'imprimer la clé privée, et de la foutre dans un voute, à la banque.


Dans l'armée, write higher, read lower.  Pattern ici ?  Comment est restreint la suppression ?  Pour effacer un service, faut être admin ? être du même niveau ?
  http://en.wikipedia.org/wiki/Bell-LaPadula_Model

Suivant le modèle, on ne peut pas *modifier* 

Overwriter un document existant, dans ce modèle là ?? service_put par exemple ?  Vérifier avec Alexandre Miege.

Hasher, utiliser la clé sans avoir la clé.  Hasher avec la date, sans pouvoir la réutiliser ?

Deux clés de groupes, une pour admin, l'autre pour pas admin.




Permissions for each function (library and via xml-rpc)
-------------------------------------------------------

All functions requires user authentication when called via XML-RPC, unless otherwise noted.

All functions can be accessed directly via the Python library with no constraints, unless otherwise noted.

Of course, a call via XML-RPC will call the library only if authentications and checks pass.

=================  ====================================  =====================================
Function name      Access via library                    Access via web (xml-rpc)
=================  ====================================  =====================================
user_add           Fails if user exists.                 Requires 'global-admin' permission.
                   Resets setup-time if timed out.
-----------------  ------------------------------------  -------------------------------------
user_setup         Must be called before 300 seconds
                   (can be configured in the .ini file
                   under the key:
                   ``sflvaut.vault.setup_timeout``)
-----------------  ------------------------------------  -------------------------------------
user_del           Removes user *directly*.              Requires 'global-admin' permission.
-----------------  ------------------------------------  -------------------------------------
user_list          Returns setup statuses, admin flags,
                   each users' groups (and admin flags)
-----------------  ------------------------------------  -------------------------------------
service_add        No group restrictions apply. Anyone
                   can add service to any group. Mind
                   that he can't necessariliy read it
                   back.
-----------------  ------------------------------------  -------------------------------------
service_del        Prevents removing services with       Requires 'global-admin' permission.
                   childs. 'global-admin' and admins
                   of all groups the service is in are
                   allowed to delete the service.
                   Otherwise, the service needs to be
                   detached first.
-----------------  ------------------------------------  -------------------------------------
service_get
-----------------  ------------------------------------  -------------------------------------
service_put        WARN: No groups constraints are    
                   enforced when updating a service.
-----------------  ------------------------------------  -------------------------------------
service_get_tree
(show)
-----------------  ------------------------------------  -------------------------------------
service_list       No cryptogram is transmitted here
-----------------  ------------------------------------  -------------------------------------
service_passwd     Prior access to password is required
                   and enforced.
-----------------  ------------------------------------  -------------------------------------
search
-----------------  ------------------------------------  -------------------------------------
customer_get
-----------------  ------------------------------------  -------------------------------------
customer_put
-----------------  ------------------------------------  -------------------------------------
customer_add
-----------------  ------------------------------------  -------------------------------------
customer_del       Deletes all it's machines and         Requires 'global-admin' permission.
                   services.  Stops if breaking service
                   cascades.
-----------------  ------------------------------------  -------------------------------------
customer_list
-----------------  ------------------------------------  -------------------------------------
machine_put                                              Anyone can update machine infos.
-----------------  ------------------------------------  -------------------------------------
machine_get
-----------------  ------------------------------------  -------------------------------------
machine_add
-----------------  ------------------------------------  -------------------------------------
machine_del        Deletes all it's services as well.    Requires 'global-admin' permission.
                   Stops if breaking service cascades.
-----------------  ------------------------------------  -------------------------------------
machine_list
-----------------  ------------------------------------  -------------------------------------
group_get
-----------------  ------------------------------------  -------------------------------------
group_put          Group admin required to hide group.
                   Group member required to modify.
-----------------  ------------------------------------  -------------------------------------
group_add          Creator of the group is granted
                   admin privs. on that group.
-----------------  ------------------------------------  -------------------------------------
group_del          Can't remove non-empty groups         Requires 'global-admin' permission.
-----------------  ------------------------------------  -------------------------------------
group_list         Hidden groups are hidden from non-
                   members, unless 'global-admin'.
-----------------  ------------------------------------  -------------------------------------
group_add_service  CRYPTO constraint: you need to have
                   a decrypted service symkey
                   (requiring your private key, and
                   previous access to service_get) to
                   add a service to any group.  The
                   vault has no means to verify the
                   consistency of your symkey.
                   Providing random symkeys will create
                   an unusable service (accessed via
                   this group).
-----------------  ------------------------------------  -------------------------------------
group_del_service  Can't detach a service if it's its
                   last group (otherwise, you lose it).
-----------------  ------------------------------------  -------------------------------------
group_add_user     You need to have a decrypted group
                   key (requiring your private key, and
                   previous access to group_add_user to
                   retrieve the user's public key, and
                   the group's encrypted private key).
                   Enforces being in the group, since
                   this is the only way you can provide
                   a validly encrypted groupkey.
                   This command trusts that the remote
                   user adding another user enters
                   valid data as a cryptgroupkey.
                   If junk is added in that field, the
                   added user simply won't be able to
                   access the group's data. Also will
                   he need to be removed and added
                   successfully to the group for
                   everything to work.
-----------------  ------------------------------------  -------------------------------------
group_del_user     Prevents from deleting yourself from  Group-admin or 'global-admin'
                   the group.                            required
                   Makes sure someone else will remain
                   in the group.
                   Makes everything possible to make
                   sure there is at least a group admin
                   left.
=================  ====================================  =====================================



What happens if the vault is compromised
----------------------------------------

If the vault is compromised on server side -- some guy ran away with the database contents, or cracked the vault server, it is still impossible for him to decrypt anything, except in the following situations:

* If the attacker also has access to a user's private key (decrypted, that is).  In that case:

  * the attacker now has access to any service the user had.  Any services in any of the groups that user was member of.

  * he still does not have access to any of the services that aren't in the user's groups.

* If the attacker holds control of the vault, and it continues to be used, he could discover these three elements, which all have limited damage at start, but grows over time:

  * When *adding a new service* (service_add), the attacker will gain knowledge of the symkey used to encrypt the secret, and the plaintext secret itself.  This would allow him to decrypt the secret in the future without any other constraint.  He could also simply save the secret!  This symkey, though, doesn't give access to any other service, only to this one.  This symkey is regenerated when the password is changed with `service_passwd`, but if he still has access to running a compromised vault, he will probably get the new service password also.

  * When *changing a service's password*, the same thing applies.  The attacker gains knowledge of both the generated symkey and the plaintext secret.

  * When *adding a new group*, the attacker can gain knowledge of the group's generated private key.  It does not give access to any service at that particular moment, but could be used after several services have been added to that group, to decrypt those services' secret.  Though, if the attacker still has control of the vault, all these services were already compromised by the two previous cases (adding a new service, and changing a service's password).


Other risks involved
--------------------

A user could create a group, having admin privileges upon creation, and set a name that could fool other users into adding services to it, by giving it the same name as already existing group for example.  If another user adds a service to that group, the creator of the group could have access to that service, even if the user didn't have access to the original group.
