#!/usr/bin/env python

import subprocess

import urwid

from util import clear_screen, string_to_args
from process import Command
from task import TaskListModel
from task_list import TaskTable, SelectableRow, TaskListBox
import event
from command_bar import CommandBar

PALETTE = [
    ('list-header', 'black', 'white'),
    ('reveal focus', 'black', 'dark cyan', 'standout'),
]

class Application():
    def __init__(self, config, task_config, reports, report):

        self.config = config
        self.task_config = task_config
        self.reports = reports
        self.report = report
        self.command = Command(self.config)
        self.event = event.Emitter()
        self.event.listen('command-bar:keypress', self.command_bar_keypress)
        self.run(self.report)

    def command_bar_keypress(self, data):
        if 'choice' in data['metadata']:
            if data['metadata']['op'] == 'quit' and data['choice']:
                self.quit()
        elif data['key'] in ('enter'):
            args = string_to_args(data['text'])
            metadata = data['metadata']
            if metadata['op'] == 'ex':
                self.ex(data['text'], data['metadata'])
            if metadata['op'] == 'add':
                self.execute_command(['task', 'add'] + args)
            if metadata['op'] == 'modify':
                # TODO: Will this break if user clicks another list item
                # before hitting enter?
                self.execute_command(['task', metadata['uuid'], 'modify'] + args)
            if metadata['op'] == 'tag':
                if self.model.task_tags(metadata['uuid'], args):
                    self.update_report()
        self.widget.focus_position = 'body'

    def key_pressed(self, key):
        # TODO: Should be 'ZZ'.
        if key in ('Q', 'Z'):
            self.quit()
        elif key in ('u'):
            self.execute_command(['task', 'undo'])
        elif key in ('q'):
            self.activate_command_bar('quit', 'Quit?', {'choice': True, 'choices': {'y': True}})
        elif key in ('t', ':'):
            edit_text = '!rw task ' if key in ('t') else None
            self.activate_command_bar('ex', ':', edit_text=edit_text)

    def on_select(self, row, size, key):
        if key in ('a'):
            self.activate_command_bar('add', 'Add: ')
            return None
        if key in ('m'):
            uuid = self.get_focused_task()
            if uuid:
                self.activate_command_bar('modify', 'Modify: ', {'uuid': uuid})
            return None
        if key in ('T'):
            uuid = self.get_focused_task()
            if uuid:
                self.activate_command_bar('tag', 'Tag: ', {'uuid': uuid})
            return None
        if key in ('e'):
            self.execute_command(['task', row.uuid, 'edit'])
            return None
        if key in ('=', 'enter'):
            self.execute_command(['task', row.uuid, 'info'], update_report=False)
            return None
        elif key in ('ctrl l'):
            self.update_report()
        return key

    def ex(self, text, metadata):
        args = string_to_args(text)
        if len(args):
            command = args.pop(0)
            if command in ('q'):
                self.quit()
            elif command in ('!', '!r', '!w', '!rw', '!wr'):
                kwargs = {}
                if command in ('!', '!w'):
                    kwargs['update_report'] = False
                if command in ('!', '!r'):
                    kwargs['confirm'] = None
                self.execute_command(args, **kwargs)
            else:
                # TODO: Display error message.
                pass

    def get_focused_task(self):
        if self.widget.focus_position == 'body':
            try:
                return self.task_list.focus.uuid
            except:
                pass
        return False

    def quit(self):
        raise urwid.ExitMainLoop()

    def build_report(self):
        self.model = TaskListModel(self.task_config, self.reports, self.report)
        self.table = TaskTable(self.task_config, self.reports[self.report], self.model.tasks, on_select=self.on_select)

        self.header = urwid.Pile([
            urwid.Text('Welcome to PYT'),
            self.table.header,
        ])
        self.footer = CommandBar(event=self.event)

    def execute_command(self, args, **kwargs):
        update_report = True
        if 'update_report' in kwargs:
            update_report = kwargs['update_report']
            kwargs.pop('update_report')
        self.loop.stop()
        self.command.result(args, **kwargs)
        if update_report:
            self.update_report()
        self.loop.start()

    def activate_command_bar(self, op, caption, metadata={}, edit_text=None):
        metadata['op'] = op
        self.footer.activate(caption, metadata, edit_text)
        self.widget.focus_position = 'footer'

    def update_report(self, report=None):
        self.build_main_widget(report)
        self.loop.widget = self.widget

    def build_main_widget(self, report=None):
        if report:
            self.report = report
        self.build_report()
        self.widget = urwid.Frame(
            self.table.listbox,
            header=self.header,
            footer=self.footer,
        )
        self.task_list = self.widget.body

    def run(self, report):
        self.build_main_widget(report)
        self.loop = urwid.MainLoop(self.widget, PALETTE, unhandled_input=self.key_pressed)
        self.loop.run()
