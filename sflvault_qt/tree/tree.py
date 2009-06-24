#!/usr/bin/env python

import sys
from PyQt4 import QtCore, QtGui

from sflvault.client import SFLvaultClient
from sflvault_qt.bar.filterbar import FilterBar
from images.qicons import *

from lib.auth import *
#token = getAuth()


class TreeItem(QtCore.QObject):
    def __init__(self, data, icon=None, parent=None):
        self.parentItem = parent
        self.itemData = data
        self.childItems = []
        self.icon = icon

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

        # Init data item tree
        parents = []
        parents.append(self.rootItem)

        if not self.research:
            self.research = "."
        all = vaultSearch(self.research, self.groups_ids)

        for custoid, custo in all["results"].items():
            parents[-1].appendChild(TreeItem([custo["name"],"c#" + custoid], Qicons("customer"), parents[-1]))
            parents.append(parents[-1].child(parents[-1].childCount() - 1))

            for machineid, machine in custo["machines"].items():
                parents[-1].appendChild(TreeItem([machine["name"],"m#" + machineid], Qicons("machine"), parents[-1]))
                parents.append(parents[-1].child(parents[-1].childCount() - 1))

                for serviceid, service in machine["services"].items():
                    protocol = service["url"].split(":")[0] 
                    parents[-1].appendChild(TreeItem([service["url"],"s#" + serviceid], Qicons(protocol, "service"), parents[-1]))

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

        item = index.internalPointer()

        if role == QtCore.Qt.DecorationRole and index.column() == 0:
            return  QtCore.QVariant(item.icon)

        if role != QtCore.Qt.DisplayRole:
            return QtCore.QVariant()

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

    def children(self, parent):
        if parent.column() > 0:
            return 0

        if not parent.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()

        return parentItem.childItems


class proxyVault(QtGui.QSortFilterProxyModel):
    def __init__(self, parent=None):
        QtGui.QSortFilterProxyModel.__init__(self, parent)
        self.setDynamicSortFilter(1)
        self.setSortCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.source_model = self.sourceModel()
        self.shown = set()
        self.match = set()

    def filterAcceptsRow(self, sourceRow, sourceParent):
        """
            Permit to filter on 2 first columns
        """
        self.source_model = self.sourceModel()
        # By name
        index_name = self.source_model.index(sourceRow,0,sourceParent)
        # By id
        index_id = self.source_model.index(sourceRow,1,sourceParent)
        # Get pattern
        pattern = unicode(self.filterRegExp().pattern())
    
        if unicode(index_id.data(0).toString()).find(pattern) != -1: 
            # Add it in shown list
            self.shown.add(index_name)
            # Add it in match list
            self.match.add(index_name)
            return True
        if unicode(index_name.data(0).toString()).find(pattern) != -1:
            # Add it in shown list
            self.shown.add(index_name)
            # Add it in match list
            self.match.add(index_name)
            return True

        # Check if parent is shown and show only if 
        # at least one of its children is going to be shown
        parent_index = self.source_model.parent(index_name)
        if parent_index in self.shown:
            # Show it if its parent match
            if parent_index in self.match:
                # Add it in shown list
                self.shown.add(index_name)
                # remove it in match list if exist in
                if index_name in self.match:
                    self.match.remove(index_name)               
                return True
            # Show it if its granpa match
            if self.source_model.parent(parent_index) in self.match:
                # Add it in shown list
                self.shown.add(index_name)
                # remove it in match list if exist in
                if index_name in self.match:
                    self.match.remove(index_name)
                return True

        # Show it if one a its child match
        for child in self.source_model.children(index_name):
            if unicode(child.data(0)).find(pattern) != -1 or unicode(child.data(1)).find(pattern) != -1:
                # Add it in shown list
                self.shown.add(index_name)
                # remove it in match list if exist in
                if index_name in self.match:
                    self.match.remove(index_name)
                return True
            # Show it if one a its little child match
            for subchild in child.childItems:
                if unicode(subchild.data(0)).find(pattern) != -1 or unicode(subchild.data(1)).find(pattern) != -1 :
                    # Add it in shown list
                    self.shown.add(index_name)
                    # remove it in match list if exist in
                    if index_name in self.match:
                        self.match.remove(index_name)
                    return True

        # remove index_name if it s in shown list
        if index_name in self.shown:
            self.shown.remove(index_name)
        # remove it in match list if exist in
        if index_name in self.match:
            self.match.remove(index_name)
        return False


class TreeView(QtGui.QTreeView):
    def __init__(self, parent=None):
        QtGui.QTreeView.__init__(self, parent)
        self.parent = parent
        # Load proxy
        self.proxyModel = proxyVault(self)
        # Set view properties
        self.setSortingEnabled(1)
        self.setModel(self.proxyModel)
        self.sortByColumn(0,QtCore.Qt.AscendingOrder)
        # Load context actions
        self.createActions()

    def setGeometries(self):
        """
            Set headers size
        """
        h = self.header()
        h.setResizeMode(0, QtGui.QHeaderView.Stretch)
        h.setStretchLastSection(0)
        self.setColumnWidth(1,65)

    def search(self, research, groups_ids=None):
        # Load model
        self.sourcemodel = TreeModel(research, groups_ids, self)
        # Load proxy
        self.proxyModel.setSourceModel(self.sourcemodel)

    def contextMenuEvent(self, event):
        """
            Create contextMenu on right click
        """
        if self.selectedIndexes():
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

        self.bookmarkAct = QtGui.QAction(self.tr("&Create alias..."), self)
        #self.bookmarkAct.setShortcut(self.tr("Ctrl+V"))
        self.bookmarkAct.setStatusTip(self.tr("Create an alias from this item"))
#        self.connect(self.reomveFileAct, QtCore.SIGNAL("triggered()"), self.remove)


    def filter(self, pattern):
        """
            Filter and expand
        """
        self.proxyModel.setFilterRegExp(pattern)
        if pattern:
            self.expandAll()
        else:
            self.collapseAll()
        

class TreeVault(QtGui.QWidget):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.parent = parent

        self.tree = TreeView(parent)
        self.filter = FilterBar(self) 
        self.filter.connect(self.filter.filter_input, QtCore.SIGNAL("textChanged(const QString&)"), self.tree.filter)

        layout = QtGui.QVBoxLayout(self);
        layout.setSpacing(0)
        layout.setMargin(0)

        layout.addWidget(self.tree)
        layout.addWidget(self.filter)

    def connection(self):
        self.tree.search(None, None)
        self.tree.setGeometries()
