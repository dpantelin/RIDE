#  Copyright 2008-2009 Nokia Siemens Networks Oyj
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import wx
from wx.lib.mixins.listctrl import TextEditMixin

from robotide.editor.listeditor import ListEditor, AutoWidthColumnList
from robotide.context import Font


_CONFIG_HELP = '\n\n'.join([ txt for txt in
'''The specified command string will be split from whitespaces into a command
and its arguments. If either the command or any of the arguments require
internal spaces, they must be written as '<SPACE>'.'''.replace('\n', ' '),
'''The command will be executed in the system directly without opening a shell.
This means that shell commands and extensions are not available. For example,
in Windows batch files to execute must contain the '.bat' extension and 'dir'
command does not work.'''.replace('\n', ' '),
'''Examples:
    pybot.bat --include smoke C:\\my_tests
    svn update /home/robot
    C:\\Program<SPACE>Files\\App\\prg.exe argument<SPACE>with<SPACE>space'''
])


class ConfigManagerDialog(wx.Dialog):
    _style = wx.DEFAULT_DIALOG_STYLE|wx.THICK_FRAME

    def __init__(self, configs):
        wx.Dialog.__init__(self, wx.GetTopLevelWindows()[0], style=self._style,
                           title='Manage Run Configurations')
        self._create_ui(configs)

    def _create_ui(self, configs):
        self.SetSizer(wx.BoxSizer(wx.VERTICAL))
        self._editor = self._create_editor(configs)
        self._create_help()
        self._create_line()
        self._create_buttons()
        self.SetSize((750, 400))

    def _create_editor(self, configs):
        editor = _ConfigListEditor(self, configs)
        self.Sizer.Add(editor, flag=wx.GROW, proportion=1)
        return editor

    def _create_help(self):
        help = wx.StaticText(self, label=_CONFIG_HELP)
        help.Wrap(700)
        help.SetFont(Font().help)
        self.Sizer.Add(help, border=5,flag=wx.TOP)

    def _create_line(self):
        line = wx.StaticLine(self, size=(20,-1), style=wx.LI_HORIZONTAL)
        self.Sizer.Add(line, border=5,
                       flag=wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.RIGHT|wx.TOP)

    def _create_buttons(self):
        self.Sizer.Add(self.CreateStdDialogButtonSizer(wx.OK|wx.CANCEL),
                       flag=wx.ALIGN_CENTER|wx.ALL, border=5)

    def get_data(self):
        return self._editor.get_data()


class _ConfigListEditor(ListEditor):
    _buttons = ['New']
    _columns = ['Name', 'Command', 'Documentation']

    def __init__(self, parent, configs):
        ListEditor.__init__(self, parent, self._columns, configs)

    def _create_list(self, columns, data):
        return _TextEditListCtrl(self, columns, data, self._new_config)

    def get_column_values(self, config):
        return config.name, config.command, config.doc

    def get_data(self):
        return self._list.get_data()

    def OnEdit(self, event):
        self._list.open_editor(self._selection)

    def OnNew(self, event):
        self._list.new_item()

    def _new_config(self, data):
        self._data.add(*data)


class _TextEditListCtrl(AutoWidthColumnList, TextEditMixin):
    last_index = property(lambda self: self.ItemCount-1)

    def __init__(self, parent, columns, data, new_item_callback):
        AutoWidthColumnList.__init__(self, parent, columns, data)
        TextEditMixin.__init__(self)
        self.col_locs = self._calculate_col_locs()
        self._new_item_callback = new_item_callback
        self._new_item_creation = False

    def _calculate_col_locs(self):
        """Calculates and returns initial locations of colums.

        This is needed so that TextEditMixin can work from context menu,
        without selecting the row first.
        """
        locations = [0]
        loc = 0
        for n in range(self.GetColumnCount()):
            loc = loc + self.GetColumnWidth(n)
            locations.append(loc)
        return locations

    def open_editor(self, row):
        self.OpenEditor(0, row)

    def new_item(self):
        self._new_item_creation = True
        self.InsertStringItem(self.ItemCount, '')
        self.open_editor(self.last_index)

    def get_data(self):
        return [ self._get_row(row) for row in range(self.ItemCount) ]

    def _get_row(self, row):
        return [ self.GetItem(row, col).GetText() for col in range(3)]

    def CloseEditor(self, event=None):
        TextEditMixin.CloseEditor(self, event)
        # It seems that this is called twice per editing action and in the
        # first time the value may be empty.
        # End new item creation only when there really is a value
        lastrow = self._get_row(self.last_index)
        if self._new_item_creation and any(lastrow):
            self._new_item_creation = False
            self._new_item_callback(lastrow)


