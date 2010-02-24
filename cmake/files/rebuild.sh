umask 022
mkdir rebuild
cd rebuild
ar x ../$1.deb
mkdir data
cd data; tar zxvf ../data.tar.gz
rm -f ../data.tar.gz
find . -type f -exec chmod 644 {} \;
find . -type d -exec chmod 755 {} \;
chmod 755 usr/bin/sflvault-client-qt4
tar zcvf ../data.tar.gz --owner=root --group=root .
cd ..
ar r ../$1.deb data.tar.gz
mkdir control
cd control
tar zxvf ../control.tar.gz
chmod 644 md5sums
tar zcvf ../control.tar.gz --owner=root --group=root .
cd ..
ar r ../$1.deb control.tar.gz
cd ..
rm -rf rebuild
