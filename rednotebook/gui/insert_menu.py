# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------
# Copyright (c) 2012  Jendrik Seipp
#
# RedNotebook is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# RedNotebook is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with RedNotebook; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
# -----------------------------------------------------------------------

import os

import gtk

from rednotebook.util import filesystem


XML = '''\
<ui>
<popup action="InsertMenu">
    <menuitem action="Picture"/>
    <menuitem action="File"/>
    <menuitem action="Link"/>
    <menuitem action="BulletList"/>
    %(numlist_ui)s
    <menuitem action="Title"/>
    <menuitem action="Line"/>
    %(table_ui)s
    %(formula_ui)s
    <menuitem action="Date"/>
    <menuitem action="LineBreak"/>
</popup>
</ui>'''


def get_image(name):
    image = gtk.Image()
    file_name = os.path.join(filesystem.image_dir, name)
    image.set_from_file(file_name)
    return image


class InsertMenu(object):
    def __init__(self, main_window):
        self.main_window = main_window

        self.bullet_list = ('\n- %s\n- %s\n  - %s (%s)\n\n\n' %
                (_('First Item'), _('Second Item'),
                 _('Indented Item'), _('Two blank lines close the list')))

        self.setup()
        
    def setup(self):
        '''
        See http://www.pygtk.org/pygtk2tutorial/sec-UIManager.html for help
        A popup menu cannot show accelerators (HIG).
        '''

        numlist_ui = '' #'<menuitem action="NumberedList"/>'
        table_ui = '' # '<menuitem action="Table"/>'
        formula_ui = '' #'<menuitem action="Formula"/>'

        insert_menu_xml = XML % locals()

        uimanager = self.main_window.uimanager

        # Add the accelerator group to the toplevel window
        accelgroup = uimanager.get_accel_group()
        self.main_window.main_frame.add_accel_group(accelgroup)

        # Create an ActionGroup
        self.main_window.insert_actiongroup = gtk.ActionGroup('InsertActionGroup')

        line = '\n====================\n'

        table = ('\n|| Whitespace Left | Whitespace Right | Resulting Alignment |\n'
                   '| 1               | more than 1     | Align left   |\n'
                   '|     more than 1 |               1 |   Align right |\n'
                   '|   more than 1   |   more than 1   |   Center   |\n'
                   '|| Title rows | are always | centered |\n'
                   '|  Use two vertical  |  lines on the left  |  for title rows  |\n'
                   '|  Always use  |  at least  |  one whitespace  |\n')

        line_break = r'\\'

        def tmpl(letter):
            return ' (Ctrl+%s)' % letter

        # Create actions
        self.main_window.insert_actiongroup.add_actions([
            ('Picture', gtk.STOCK_ORIENTATION_PORTRAIT, _('Picture'),
                None, _('Insert an image from the harddisk'),
                self.get_insert_handler(self.on_insert_pic)),
            ('File', gtk.STOCK_FILE, _('File'), None,
                _('Insert a link to a file'),
                self.get_insert_handler(self.on_insert_file)),
            ### Translators: Noun
            ('Link', gtk.STOCK_JUMP_TO, _('_Link') + tmpl('L'), '<Control>L',
                _('Insert a link to a website'),
                self.get_insert_handler(self.on_insert_link)),
            ('BulletList', None, _('Bullet List'), None, None,
                self.get_insert_handler(self.on_insert_bullet_list)),
            ('NumberedList', None, _('Numbered List'), None, None,
                self.get_insert_handler(self.on_insert_numbered_list)),
            ('Title', None, _('Title'), None, None,
                self.get_insert_handler(self.on_insert_title)),
            ('Line', None, _('Line'), None,
                _('Insert a separator line'),
                self.get_insert_handler(lambda sel_text: line)),
            ('Table', None, _('Table'), None, None,
                self.get_insert_handler(lambda sel_text: table)),
            ('Formula', None, _('Latex Formula'), None, None,
                self.get_insert_handler(self.on_insert_formula)),
            ('Date', None, _('Date/Time') + tmpl('D'), '<Ctrl>D',
                _('Insert the current date and time (edit format in preferences)'),
                self.get_insert_handler(self.on_insert_date_time)),
            ('LineBreak', None, _('Line Break'), None,
                _('Insert a manual line break'),
                self.get_insert_handler(lambda sel_text: line_break)),
            ])

        # Add the actiongroup to the uimanager
        uimanager.insert_action_group(self.main_window.insert_actiongroup, 0)

        # Add a UI description
        uimanager.add_ui_from_string(insert_menu_xml)

        # Create a Menu
        menu = uimanager.get_widget('/InsertMenu')

        image_items = 'Picture Link BulletList Title Line Date LineBreak Table'.split()

        for item in image_items:
            menu_item = uimanager.get_widget('/InsertMenu/'+ item)
            filename = item.lower()
            # We may have disabled menu items
            if menu_item:
                menu_item.set_image(get_image(filename + '.png'))

        self.main_window.single_menu_toolbutton = gtk.MenuToolButton(gtk.STOCK_ADD)
        self.main_window.single_menu_toolbutton.set_label(_('Insert'))

        self.main_window.single_menu_toolbutton.set_menu(menu)
        self.main_window.single_menu_toolbutton.connect('clicked', self.show_insert_menu)
        self.main_window.single_menu_toolbutton.set_tooltip_text(_('Insert images, files, links and other content'))
        edit_toolbar = self.main_window.builder.get_object('edit_toolbar')
        edit_toolbar.insert(self.main_window.single_menu_toolbutton, -1)
        self.main_window.single_menu_toolbutton.show()

    def get_insert_handler(self, func):
        def insert_handler(widget):
            sel_text = self.main_window.day_text_field.get_selected_text()
            repl = func(sel_text)
            if isinstance(repl, basestring):
                self.main_window.day_text_field.replace_selection(repl)
            elif isinstance(repl, tuple):
                self.main_window.day_text_field.replace_selection_and_highlight(*repl)
            else:
                assert repl is None, repl
        return insert_handler

    def show_insert_menu(self, button):
        '''
        Show the insert menu, when the Insert Button is clicked.

        A little hack for button and activate_time is needed as the "clicked" does
        not have an associated event parameter. Otherwise we would use event.button
        and event.time
        '''
        self.main_window.single_menu_toolbutton.get_menu().popup(parent_menu_shell=None,
                            parent_menu_item=None, func=None, button=0, activate_time=0, data=None)

    def on_insert_pic(self, sel_text):
        dirs = self.main_window.journal.dirs
        picture_chooser = self.main_window.builder.get_object('picture_chooser')
        picture_chooser.set_current_folder(dirs.last_pic_dir)

        filter = gtk.FileFilter()
        filter.set_name("Images")
        filter.add_mime_type("image/png")
        filter.add_mime_type("image/jpeg")
        filter.add_mime_type("image/gif")
        filter.add_pattern("*.png")
        filter.add_pattern("*.jpg")
        filter.add_pattern("*.jpeg")
        filter.add_pattern("*.gif")
        filter.add_pattern("*.bmp")

        picture_chooser.add_filter(filter)

        # Add box for inserting image width.
        box = gtk.HBox()
        box.set_spacing(2)
        label = gtk.Label(_('Width (optional):'))
        width_entry = gtk.Entry(max=6)
        width_entry.set_width_chars(6)
        box.pack_start(label, False)
        box.pack_start(width_entry, False)
        box.pack_start(gtk.Label(_('pixels')), False)
        box.show_all()
        picture_chooser.set_extra_widget(box)

        response = picture_chooser.run()
        picture_chooser.hide()

        if response == gtk.RESPONSE_OK:
            dirs.last_pic_dir = picture_chooser.get_current_folder().decode('utf-8')
            base, ext = os.path.splitext(picture_chooser.get_filename().decode('utf-8'))

            # On windows firefox accepts absolute filenames only
            # with the file:// prefix
            base = filesystem.get_local_url(base)

            width_text = ''
            width = width_entry.get_text().decode('utf-8')
            if width:
                try:
                    width = int(width)
                except ValueError:
                    self.main_window.journal.show_message(_('Width must be an integer.'), error=True)
                    return
                width_text = '?%d' % width

            if sel_text:
                sel_text = ' ' + sel_text
            return '[%s""%s""%s%s]' % (sel_text, base, ext, width_text)

    def on_insert_file(self, sel_text):
        dirs = self.main_window.journal.dirs
        file_chooser = self.main_window.builder.get_object('file_chooser')
        file_chooser.set_current_folder(dirs.last_file_dir)

        response = file_chooser.run()
        file_chooser.hide()

        if response == gtk.RESPONSE_OK:
            dirs.last_file_dir = file_chooser.get_current_folder().decode('utf-8')
            filename = file_chooser.get_filename().decode('utf-8')
            filename = filesystem.get_local_url(filename)
            sel_text = self.main_window.day_text_field.get_selected_text()
            head, tail = os.path.split(filename)
            # It is always safer to add the "file://" protocol and the ""s
            return '[%s ""%s""]' % (sel_text or tail, filename)

    def on_insert_link(self, sel_text):
        link_creator = self.main_window.builder.get_object('link_creator')
        link_location_entry = self.main_window.builder.get_object('link_location_entry')
        link_name_entry = self.main_window.builder.get_object('link_name_entry')

        link_location_entry.set_text('http://')
        link_name_entry.set_text(sel_text)

        def link_entered():
            return bool(link_location_entry.get_text())

        def on_link_changed(widget):
            # Only make the link submittable, if text has been entered.
            link_creator.set_response_sensitive(gtk.RESPONSE_OK, link_entered())

        link_location_entry.connect('changed', on_link_changed)

        # Let user finish by hitting ENTER.
        def respond(widget):
            if link_entered():
                link_creator.response(gtk.RESPONSE_OK)

        link_location_entry.connect('activate', respond)
        link_name_entry.connect('activate', respond)

        link_location_entry.grab_focus()

        response = link_creator.run()
        link_creator.hide()

        if response == gtk.RESPONSE_OK:
            link_location = link_location_entry.get_text()
            link_name = link_name_entry.get_text()

            if link_location and link_name:
                return '[%s ""%s""]' % (link_name, link_location)
            elif link_location:
                return link_location
            else:
                self.main_window.journal.show_message(_('No link location has been entered'), error=True)

    def on_insert_bullet_list(self, sel_text):
        if sel_text:
            return '\n'.join('- %s' % row for row in sel_text.splitlines())
        return self.bullet_list

    def on_insert_numbered_list(self, sel_text):
        if sel_text:
            return '\n'.join('+ %s' % row for row in sel_text.splitlines())
        return self.bullet_list.replace('-', '+')

    def on_insert_title(self, sel_text):
        return '\n=== ', sel_text or _('Header'), ' ===\n'

    def on_insert_formula(self, sel_text):
        formula = sel_text or '\\sum_{i=1}^n i = \\frac{n(n+1)}{2}'
        return '\\(', formula, '\\)'

    def on_insert_date_time(self, sel_text):
        format_string = self.main_window.journal.config.read('dateTimeString', '%A, %x %X')
        return dates.format_date(format_string)