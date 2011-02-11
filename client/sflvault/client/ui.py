# -=- encoding: utf-8 -=-
#
# SFLvault - Secure networked password store and credentials manager.
#
# Copyright (C) 2008  Savoir-faire Linux inc.
#
# Author: Alexandre Bourget <alexandre.bourget@savoirfairelinux.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


"""ui.py includes all graphical user interfaces (mostly console based)
to manage SFLvault elements (customers, machines, services)
"""

import platform
if platform.system() != 'Windows':
    import urwid
    import urwid.raw_display

class DialogExit(Exception):
    pass


class DialogDisplay(object):
    palette = [
        ('body',       'black','light gray','standout'),
        ('border',     'black','dark blue'),
        ('shadow',     'white','black'),
        ('selectable', 'black','dark cyan'),
        ('focus',      'white','dark blue','bold'),
        ('focustext',  'light gray','dark blue'),
        ('editfc',     'white','dark blue','bold'),
        ('editbx',     'light gray','dark blue'),
        ('editcp',     'black','light gray','standout'),
        ]


    def __init__(self, text, height, width, body=None):
        width = int(width)
        if width <= 0:
            width = ('relative', 80)
        height = int(height)
        if height <= 0:
            height = ('relative', 80)

        self.body = body
        if body is None:
            # fill space with nothing
            body = urwid.Filler(urwid.Divider(),'top')

        self.frame = urwid.Frame( body, focus_part='footer')
        if text is not None:
            self.frame.header = urwid.Pile( [urwid.Text(text),
                    urwid.Divider()] )
        w = self.frame

        # pad area around listbox
        w = urwid.Padding(w, ('fixed left',2), ('fixed right',2))
        w = urwid.Filler(w, ('fixed top',1), ('fixed bottom',1))
        w = urwid.AttrWrap(w, 'body')

        # "shadow" effect
        w = urwid.Columns( [w,('fixed', 2, urwid.AttrWrap(
                urwid.Filler(urwid.Text(('border','  ')), "top")
                ,'shadow'))])
        w = urwid.Frame( w, footer = 
                urwid.AttrWrap(urwid.Text(('border','  ')),'shadow'))

        # outermost border area
        w = urwid.Padding(w, 'center', width )
        w = urwid.Filler(w, 'middle', height )
        w = urwid.AttrWrap( w, 'border' )

        self.view = w


    def add_buttons(self, buttons):
        l = []
        for name, exitcode in buttons:
            b = urwid.Button(name, self.button_press)
            b.exitcode = exitcode
            b = urwid.AttrWrap(b, 'selectable', 'focus')
            l.append(b)
        self.buttons = urwid.GridFlow(l, 10, 3, 1, 'center')
        self.frame.footer = urwid.Pile([urwid.Divider(),
                                        self.buttons],
                                       focus_item = 1)

    def button_press(self, button):
        raise DialogExit(button.exitcode)

    def main(self):
        self.ui = urwid.raw_display.Screen()
        self.ui.register_palette( self.palette )
        return self.ui.run_wrapper( self.show_dialog )

    def show_dialog(self):
        self.ui.set_mouse_tracking()
        size = self.ui.get_cols_rows()
        try:
            while True:
                canvas = self.view.render( size, focus=True )
                self.ui.draw_screen( size, canvas )
                keys = None
                while not keys: 
                    keys = self.ui.get_input()
                for k in keys:
                    if urwid.is_mouse_event(k):
                        event, button, col, row = k
                        self.view.mouse_event( size, 
                                event, button, col, row,
                                focus=True)
                    if k == 'window resize':
                        size = self.ui.get_cols_rows()
                    k = self.view.keypress( size, k )

                    if k:
                        self.unhandled_key( size, k)
                        
        except DialogExit, e:
            return self.on_exit( e.args[0] )

    def on_exit(self, exitcode):
        return exitcode, ""

    def unhandled_key(self, size, k):
        if k in ('up','page up'):
            self.frame.set_focus('body')
        if k in ('down','page down'):
            self.frame.set_focus('footer')
        if k == 'enter':
            # pass enter to the "ok" button
            self.frame.set_focus('footer')
            self.buttons.set_focus(0)
            self.view.keypress( size, k )




##
##
## Local dialogs for SFLvault
##
##

class ServiceEditDialogDisplay(DialogDisplay):
    """Edit a service"""
    def __init__(self, data):
        # Temporarily disabled. We'll look into editing right here the groups
        # at anothe moment. We must be able to edit services right now.
        #
        #groups = [urwid.CheckBox('Tag', False, user_data=1),
        #          urwid.CheckBox('tag2', True, user_data=2),
        #          urwid.CheckBox('tag 3', False, user_data=3)]

        metadata_str = '\n'.join('%s=%s' % (key, val) for key, val in data['metadata'].items()) + '\n'
        inputs = {'url': urwid.Edit("", str(data['url']), wrap='clip'),
                  'machine_id': urwid.Edit("", str(data['machine_id'] or '')),
                  'parent_service_id': urwid.Edit("", str(data['parent_service_id'] or '')),
                  'notes': urwid.Edit("", str(data['notes'])),
                  'metadata': urwid.Edit("", metadata_str, multiline=True)
                  }
                  
                
        
        l = [
            urwid.Columns([('fixed', 15, urwid.Text('URL ', align="right")),
                  urwid.AttrWrap(inputs['url'], 'editbx', 'editfc' )]),
            
            urwid.Columns([('fixed', 15, urwid.Text('Machine ID ',
                                                    align="right")),
                  urwid.AttrWrap(inputs['machine_id'], 'editbx', 'editfc')]),
            
            urwid.Columns([('fixed', 15, urwid.Text('Parent service ID ',
                                                    align="right")),
                  urwid.AttrWrap(inputs['parent_service_id'],
                                 'editbx', 'editfc')]),
            
            urwid.Columns([('fixed', 15, urwid.Text('Notes ', align="right")),
                  urwid.AttrWrap(inputs['notes'], 'editbx','editfc' )]),
            urwid.Divider(),
            urwid.Columns([('fixed', 15, urwid.Text('Metadata ', align="right")),
                           urwid.AttrWrap(inputs['metadata'], 'editbx', 'editfc')])
            
            # Temp disabled (read above)
            #urwid.Divider(),
            #urwid.Columns([('fixed', 15, urwid.Text('Groups ', align="right")),
            #               urwid.AttrWrap(urwid.Pile(groups, 1), 'selectable')])
            ]


        walker = urwid.SimpleListWalker(l)
        lb = urwid.ListBox( walker )
        DialogDisplay.__init__(self, "Edit service", 22, 70, lb)

        self.frame.set_focus('body')
        
        self.add_buttons([("OK", 1), ("Cancel", 0)])

        self.data = data
        self.inputs = inputs

    def run(self):
        """Show the dialog box, and get the results afterwards."""

        exitcode, exitstring = self.main()

        if exitcode:
            data = {}
            # prepare to save
            t = ['parent_service_id', 'machine_id', 'url', 'notes']
            for x in t:
                if self.inputs[x].edit_text != self.data[x]:
                    data[x] = self.inputs[x].edit_text
            metadata = {}
            for line in self.inputs['metadata'].edit_text.split('\n'):
                parts = line.split('=', 1)
                if len(parts) == 2:
                    metadata[parts[0].strip()] = parts[1].strip()
            data['metadata'] = metadata
            return True, data
        else:
            # return nothing..
            return False, None



class MachineEditDialogDisplay(DialogDisplay):
    """Edit a machine"""
    def __init__(self, data):

        # Create fields..
        inputs = {'customer_id': urwid.Edit("", str(data['customer_id'] or ''))}
        for x in ['ip', 'name', 'fqdn', 'location', 'notes']:
            inputs[x] = urwid.Edit("", str(data[x])) # , wrap='clip'
                  
        l = [
            urwid.Columns([('fixed', 15, urwid.Text('Customer ID ',
                                                    align="right")),
                  urwid.AttrWrap(inputs['customer_id'], 'editbx', 'editfc')]),
            
            urwid.Columns([('fixed', 15, urwid.Text('Name ', align="right")),
                  urwid.AttrWrap(inputs['name'], 'editbx', 'editfc' )]),
            
            urwid.Columns([('fixed', 15, urwid.Text('IP ', align="right")),
                  urwid.AttrWrap(inputs['ip'], 'editbx', 'editfc' )]),
            
            urwid.Columns([('fixed', 15, urwid.Text('FQDN ', align="right")),
                  urwid.AttrWrap(inputs['fqdn'], 'editbx', 'editfc' )]),
            
            urwid.Columns([('fixed', 15, urwid.Text('Location ',
                                                    align="right")),
                  urwid.AttrWrap(inputs['location'], 'editbx', 'editfc' )]),
            
            urwid.Columns([('fixed', 15, urwid.Text('Notes ', align="right")),
                  urwid.AttrWrap(inputs['notes'], 'editbx','editfc' )]),
            

            ]


        walker = urwid.SimpleListWalker(l)
        lb = urwid.ListBox( walker )
        DialogDisplay.__init__(self, "Edit machine", 22, 70, lb)

        self.frame.set_focus('body')
        
        self.add_buttons([("OK", 1), ("Cancel", 0)])

        self.data = data
        self.inputs = inputs



    def run(self):
        """Show the dialog box, and get the results afterwards."""

        exitcode, exitstring = self.main()

        if exitcode:
            data = {}
            # prepare to save
            t = ['customer_id', 'ip', 'name', 'fqdn', 'location', 'notes']
            for x in t:
                if self.inputs[x].edit_text != self.data[x]:
                    data[x] = self.inputs[x].edit_text

            return True, data
        else:
            # return nothing..
            return False, None




class CustomerEditDialogDisplay(DialogDisplay):
    """Edit a customer"""
    def __init__(self, data):

        # Create fields..
        inputs = {}
        for x in ['name']:
            inputs[x] = urwid.Edit("", unicode(data[x])) # , wrap='clip'
                  
        l = [
            urwid.Columns([('fixed', 15, urwid.Text('Name ',
                                                    align="right")),
                           urwid.AttrWrap(inputs['name'], 'editbx', 'editfc')]),
            ]


        walker = urwid.SimpleListWalker(l)
        lb = urwid.ListBox( walker )
        DialogDisplay.__init__(self, "Edit customer", 22, 70, lb)

        self.frame.set_focus('body')
        
        self.add_buttons([("OK", 1), ("Cancel", 0)])

        self.data = data
        self.inputs = inputs



    def run(self):
        """Show the dialog box, and get the results afterwards."""

        exitcode, exitstring = self.main()

        if exitcode:
            data = {}
            # prepare to save
            t = ['name']
            for x in t:
                if self.inputs[x].edit_text != self.data[x]:
                    data[x] = self.inputs[x].edit_text

            return True, data
        else:
            # return nothing..
            return False, None


class GroupEditDialogDisplay(DialogDisplay):
    """Edit a group"""
    def __init__(self, data):

        # Create fields..
        inputs = {}
        # TODO: Eventually add 'hidden' to tweak hidden status.
        for x in ['name']:
            inputs[x] = urwid.Edit("", unicode(data[x])) # , wrap='clip'
                  
        l = [
            urwid.Columns([('fixed', 15, urwid.Text('Name ',
                                                    align="right")),
                           urwid.AttrWrap(inputs['name'], 'editbx', 'editfc')]),
            ]


        walker = urwid.SimpleListWalker(l)
        lb = urwid.ListBox( walker )
        DialogDisplay.__init__(self, "Edit group", 22, 70, lb)

        self.frame.set_focus('body')
        
        self.add_buttons([("OK", 1), ("Cancel", 0)])

        self.data = data
        self.inputs = inputs



    def run(self):
        """Show the dialog box, and get the results afterwards."""

        exitcode, exitstring = self.main()

        if exitcode:
            data = {}
            # prepare to save
            t = ['name']
            for x in t:
                if self.inputs[x].edit_text != self.data[x]:
                    data[x] = self.inputs[x].edit_text

            return True, data
        else:
            # return nothing..
            return False, None

