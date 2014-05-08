PKG_PREFIX=sflvault-

DIR_DEB=deb
DIR_RPM=rpm
DIR_COMMON=common
DIR_CLIENT=client
DIR_CLIENT_QT=client-qt
DIR_SERVER=server

include build-scripts/functions.mk

all: common-deb-pkg client-deb-pkg client-qt-deb-pkg server-deb-pkg
	@echo
	@echo "sflvault has been fully built"
	@find $(DIR_DEB)

all-src: all-rpm-src all-deb-src

all-rpm-src: common-rpm-src client-rpm-src client-qt-rpm-src server-rpm-src

all-deb-src: common-deb-src client-deb-src client-qt-deb-src server-deb-src

clean: common-clean client-clean client-qt-clean server-clean

distclean: clean common-distclean client-distclean client-qt-distclean server-distclean
	rm -rf $(DIR_DEB)
	rm -rf $(DIR_RPM)


common-clean:
	$(call package-clean,common)

common-distclean:
	$(call package-distclean,common)

common-rpm-src: common-clean
	$(call package-rpm-src,common)

common-rpm-bin: common-rpm-src
	$(call package-rpm-bin,common)

common-deb-src: common-clean
	$(call package-deb-src,common)

common-deb-bin: common-deb-src
	$(call package-deb-bin,common)


client-clean:
	$(call package-clean,client)

client-distclean:
	$(call package-distclean,client)

client-rpm-src: client-clean
	$(call package-rpm-src,client)

client-rpm-bin: client-rpm-src
	$(call package-rpm-bin,client)

client-deb-src: client-clean
	$(call package-deb-src,client)

client-deb-bin: client-deb-src
	$(call package-deb-bin,client)


client-qt-clean:
	$(call package-clean,client-qt)

client-qt-distclean:
	$(call package-distclean,client-qt)

client-qt-rpm-src: client-qt-clean
	$(call package-rpm-src,client-qt)

client-qt-rpm-bin: client-qt-rpm-src
	$(call package-rpm-bin,client-qt)

client-qt-deb-src: client-qt-clean
	$(call package-deb-src,client-qt)

client-qt-deb-bin: client-qt-deb-src
	$(call package-deb-bin,client-qt)


server-clean:
	$(call package-clean,server)

server-distclean:
	$(call package-distclean,server)

server-rpm-src: server-clean
	$(call package-rpm-src,server)

server-rpm-bin: server-rpm-src
	$(call package-rpm-bin,server)

server-deb-src: server-clean
	$(call package-deb-src,server)

server-deb-bin: server-deb-src
	$(call package-deb-bin,server)

