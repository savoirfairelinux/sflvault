#!/usr/bin/env python

import sys
from PyQt4 import QtCore, QtGui

from sflvault.client import SFLvaultClient

from auth import auth
token = auth.getAuth()



class TreeItem:
    def __init__(self, data, parent=None):
        self.parentItem = parent
        self.itemData = data
        self.childItems = []

    def appendChild(self, item):
        self.childItems.append(item)

    def child(self, row):
        return self.childItems[row]

    def childCount(self):
        return len(self.childItems)

    def columnCount(self):
        return len(self.itemData)

    def data(self, column):
        return self.itemData[column]

    def parent(self):
        return self.parentItem

    def row(self):
        if self.parentItem:
            return self.parentItem.childItems.index(self)

        return 0


class TreeModel(QtCore.QAbstractItemModel):
    def __init__(self, research=None, groups_ids=None, parentView=None):
        QtCore.QAbstractItemModel.__init__(self, parentView)
        self.parentView = parentView

        rootData = []
        rootData.append(QtCore.QVariant("Name"))
        rootData.append(QtCore.QVariant("Id"))
        self.rootItem = TreeItem(rootData)
        self.research = research
        self.groups_ids = groups_ids
        global token

        # Init data item tree
        parents = []
        parents.append(self.rootItem)

        if not self.research:
            self.research = "."
        all = token.vault.search(token.authtok, self.research, self.groups_ids)


        for custoid, custo in all["results"].items():
            parents[-1].appendChild(TreeItem([custo["name"],int(custoid)], parents[-1]))
            parents.append(parents[-1].child(parents[-1].childCount() - 1))

            for machineid, machine in custo["machines"].items():
                parents[-1].appendChild(TreeItem([machine["name"],int(machineid)], parents[-1]))
                parents.append(parents[-1].child(parents[-1].childCount() - 1))

                for serviceid, service in machine["services"].items():
                    parents[-1].appendChild(TreeItem([service["url"],int(serviceid)], parents[-1]))

                parents.pop()

            parents.pop()




    def columnCount(self, parent):
        if parent.isValid():
            return parent.internalPointer().columnCount()
        else:
            return self.rootItem.columnCount()

    def data(self, index, role):
        if not index.isValid():
            return QtCore.QVariant()

        if role != QtCore.Qt.DisplayRole:
            return QtCore.QVariant()

        item = index.internalPointer()

        return QtCore.QVariant(item.data(index.column()))

    def flags(self, index):
        if not index.isValid():
            return QtCore.Qt.ItemIsEnabled

        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

    def headerData(self, section, orientation, role):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return self.rootItem.data(section)

        return QtCore.QVariant()

    def index(self, row, column, parent):
        if row < 0 or column < 0 or row >= self.rowCount(parent) or column >= self.columnCount(parent):
            return QtCore.QModelIndex()

        if not parent.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()

        childItem = parentItem.child(row)
        if childItem:
            return self.createIndex(row, column, childItem)
        else:
            return QtCore.QModelIndex()

    def parent(self, index):
        if not index.isValid():
            return QtCore.QModelIndex()

        childItem = index.internalPointer()
        parentItem = childItem.parent()

        if parentItem == self.rootItem:
            return QtCore.QModelIndex()

        if parentItem != None:
            return self.createIndex(parentItem.row(), 0, parentItem)
        else:
            return QtCore.QModelIndex()

    def rowCount(self, parent):
        if parent.column() > 0:
            return 0

        if not parent.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()

        return parentItem.childCount()


class proxyVault(QtGui.QSortFilterProxyModel):
    def __init__(self, parent=None):
        QtGui.QSortFilterProxyModel.__init__(self, parent)
        self.setDynamicSortFilter(1)
        self.setSortCaseSensitivity(QtCore.Qt.CaseInsensitive)


    def afilterAcceptsRow(self, sourceRow, sourceParent):
        print "=============================="
#        print sourceParent.child(0,0)
#        print sourceParent
        index = self.sourceModel().index(sourceRow,0,sourceParent)
        print unicode(sourceParent.data(0).toString())
        print unicode(index.data(0).toString())
        if unicode(index.data(0).toString()).find("ns13") != -1 :
            print "GOOOG"
            return True
        return False


    def bfilterAcceptsRow(self, sourceRow, sourceParent):
        if sourceParent.isValid() and self.sourceModel().data(sourceParent,QtCore.Qt.DisplayRole).toString().contains("ns13"):
            return true

        data = self.sourceModel().data(self.sourceModel().index(sourceRow, 0, sourceParent),QtCore.Qt.DisplayRole).toString()
        ret = data.contains("ns13")

        subIndex = self.sourceModel().index(sourceRow, 0, sourceParent);
        if subIndex.isValid():
            for i in range(self.sourceModel().rowCount(subIndex)):
                ret = ret or QtGui.QSortFilterProxyModel.filterAcceptsRow(self, i, subIndex);
        return ret;


    def ifilterAcceptsRow(self, sourceRow, sourceParent):
        print "=============================="
#        print sourceParent.child(0,0)
#        print sourceParent
        index = self.sourceModel().index(sourceRow,0,sourceParent)
        print unicode(sourceParent.data(0).toString())
        print unicode(index.data(0).toString())
        #if unicode(index.data(0).toString()).find("ns13") == -1:
        #    return False
        #else:
        #    return True
        # get text from uderlying source model
        item_text = unicode(self.sourceModel().data(index,QtCore.Qt.DisplayRole).toString())
        # get what user is typed in comboBox
#        typed_text = str(self.gui.autoCombo.lineEdit().text())
        typed_text = unicode("ns13")
        # if typed text in item_text - then this item is Ok to show in
        # resulting filtering model
        if self.sourceModel().hasChildren(index):
#            print sourceParent.data(0).toString()
           # return self.filterAcceptsRow( sourceRow, sourceParent.child(0,0))
        #    print "===============" + item_text + "==================="
        #    print index.child(0,0).data(0).toString()
            plop = QtGui.QSortFilterProxyModel.filterAcceptsRow(self, sourceRow, index.child(0,0))
       #     print plop
            return plop
        elif item_text.find(typed_text) == -1:
      #      print "False : "+ item_text
            return False
        else:
       #     print "True : " + item_text
            return True

    def dfilterAcceptsRow(self,row, _parent):
        baseClass = QtGui.QSortFilterProxyModel
        baseAccepts = baseClass.filterAcceptsRow(self, row, parent)
        acceptTypes = self.acceptTypes
        if acceptTypes is None:
            return baseAccepts
        message = self.messages[row]
        return message.typeName in acceptTypes and baseAccepts
#        index = self.parent.sourcemodel.index(source_row, 0, source_parent)
#        if (self.parent.sourcemodel.hasChildren(index)):
#            return True 
#        return QtGui.QSortFilterProxyModel.filterAcceptsRow(self,source_row, source_parent)

class TreeVault(QtGui.QTreeView):
    def __init__(self, parent=None):
        QtGui.QTreeView.__init__(self, parent)
        self.parent = parent
        # Load model
        self.sourcemodel = TreeModel(None, None, self)
        # Load proxy
        self.proxyModel = proxyVault(self)
        self.proxyModel.setSourceModel(self.sourcemodel)
        # Set view properties
        self.setSortingEnabled(1)
        self.setModel(self.proxyModel)
        self.setWindowTitle("Simple Tree Model")
        self.sortByColumn(0,QtCore.Qt.AscendingOrder)
        self.setAnimated(1)
#        self.resizeColumnToContents(0)
        # Set headers
        h = self.header()
        h.setResizeMode(0, QtGui.QHeaderView.Interactive)
        h.setResizeMode(1, QtGui.QHeaderView.Interactive)
        h.setResizeMode(1, QtGui.QHeaderView.Stretch)
        h.resizeSection(0,400)
        h.resizeSection(1,70)
        # Load context actions
        self.createActions()

    def search(self, research, groups_ids):
        self.sourcemodel = TreeModel(research, groups_ids, self)
        self.proxyModel.setSourceModel(self.sourcemodel)
        self.expandAll()

    def contextMenuEvent(self, event):
        """
            Create contextMenu on right click
        """
        menu = QtGui.QMenu(self)
        menu.addAction(self.editAct)
        # Add bookmark menu for services
        if self.selectedIndexes()[0].parent().parent().isValid():
            menu.addAction(self.bookmarkAct)
        menu.exec_(event.globalPos())

    def createActions(self):
        """
            Create actions for contextMenu
        """
        self.editAct = QtGui.QAction(self.tr("&Edit..."), self)
        #self.editAct.setShortcut(self.tr("Ctrl+X"))
        self.editAct.setStatusTip(self.tr("Edit item"))
#        self.connect(self.editAct, QtCore.SIGNAL("triggered()"), self.mkdir)

        self.bookmarkAct = QtGui.QAction(self.tr("&Bookmark..."), self)
        #self.bookmarkAct.setShortcut(self.tr("Ctrl+V"))
        self.bookmarkAct.setStatusTip(self.tr("Add item to bookmark"))
#        self.connect(self.reomveFileAct, QtCore.SIGNAL("triggered()"), self.remove)

