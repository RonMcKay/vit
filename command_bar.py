import urwid

class CommandBar(urwid.Edit):
    """Custom urwid.Edit class for the command bar.
    """
    def __init__(self, **kwargs):
        self.event = kwargs['event']
        self.metadata = None
        kwargs.pop('event')
        return super().__init__(**kwargs)

    def keypress(self, size, key):
        """Overrides Edit.keypress method.
        """
        # TODO: Readline edit shortcuts.
        if key in ('enter', 'esc'):
            text = self.get_edit_text()
            data = {
                'key': key,
                'text': text,
                'metadata': self.get_metadata(),
            }
            self.set_caption('')
            self.set_edit_text('')
            self.set_metadata(None)
            self.event.emit('command-bar:keypress', data)
            return True
        return super().keypress(size, key)

    def get_metadata(self):
        return self.metadata.copy() if self.metadata else None

    def set_metadata(self, metadata):
        self.metadata = metadata

