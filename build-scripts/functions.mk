define package-clean
	rm -rf $(1)/dist
	rm -rf $(1)/deb_dist
	rm -rf $(1)/*.egg-info
endef

define package-distclean
	rm -rf $(DIR_DEB)/$(PKG_PREFIX)$(1)
endef

define package-deb-src
	mkdir -pv $(1)/debian
	cp pydist-overrides $(1)/debian/
	cd $(1) && python setup.py --command-packages=stdeb.command sdist_dsc
	rm -rf $(1)/debian
	mkdir -pv $(DIR_DEB)/$(PKG_PREFIX)$(1)
	cp -vf $(1)/deb_dist/$(PKG_PREFIX)$(1)*.tar.gz $(DIR_DEB)/$(PKG_PREFIX)$(1)/
	cp -vf $(1)/deb_dist/$(PKG_PREFIX)$(1)*.dsc    $(DIR_DEB)/$(PKG_PREFIX)$(1)/
endef

define package-deb-bin
	mkdir $(1)/debian
	cp pydist-overrides $(1)/debian/
	cd $(1) && python setup.py --command-packages=stdeb.command bdist_deb
	rm -rf $(1)/debian
	mkdir -pv $(DIR_DEB)/$(PKG_PREFIX)$(1)
	cp -vf $(1)/deb_dist/$(PKG_PREFIX)$(1)*.deb $(DIR_DEB)/$(PKG_PREFIX)$(1)/
endef

