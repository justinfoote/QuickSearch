from collections import defaultdict
import os
import re
import sublime
import sublime_plugin


class FindInFileCommand(sublime_plugin.TextCommand):
    """A first attempt at find all in the current file
    """

    def run(self, *args):
        resultsPane = self._getResultsPane()
        if resultsPane is None:
            return False

        toFind = re.escape(self._getSelectedWord())

        edit = resultsPane.begin_edit()
        try:
            regions = self.view.find_all('%s' % toFind)
            
            resultsPane.erase(edit, sublime.Region(0, resultsPane.size()))

            self._append(resultsPane, edit, self.view.file_name() + ":\n")
            if toFind is None:
                return False

            lines = defaultdict(list)
            for r in regions:
                line = self.view.rowcol(r.begin())[0]
                lines[line] += [r]
                for i in range(line - 2, line + 3):
                    # merely addressing the lines will ensure they are included
                    # in the output
                    lines[i]

            toAppend = []
            lastLine = None
            for lineNumber in sorted(lines):
                if lastLine and lineNumber > lastLine + 1:
                    toAppend.append('\n   ..\n')
                lastLine = lineNumber

                lineText = self.view.substr(self.view.line(
                        self.view.text_point(lineNumber, 0)))
                

                toAppend.append(self._format('%s' % (lineNumber + 1),
                        lineText, bool(lines[lineNumber])))

            self._append(resultsPane, edit, '\n'.join(toAppend))
        finally:
            resultsPane.end_edit(edit)

        toHighlight = resultsPane.find_all(toFind)
        resultsPane.add_regions('find_results', toHighlight, 'found', '', 
                sublime.DRAW_OUTLINED)


    def _getSelectedWord(self):
        return (self.view.substr(self.view.sel()[0]) 
                if len(self.view.sel()) == 1
                else None)


    def _doFind(self, toFind):
        selections = self.view.sel()
        if len(selections) != 1:
            return None

        toFind = self.view.substr(selections[0])

        return self.view.find_all(toFind)

    def _getResultsPane(self):
        """Returns the results pane; creating one if necessary
        """
        window = self.view.window()

        resultsPane = [v for v in window.views() 
            if v.name() == 'Find Results']

        if resultsPane:
            v = resultsPane[0]
        else:
            v = window.new_file()
            v.set_name('Find Results')
            v.settings().set('syntax', os.path.join(
                    sublime.packages_path(), 'Default', 
                    'Find Results.hidden-tmLanguage'))
            v.settings().set('draw_indent_guides', False)
            v.set_scratch(True)

        window.focus_view(v)
        window.focus_view(self.view)
        return resultsPane[0]


    def _format(self, lineNumber, line, match = False):
        spacer = ' ' * (4 - len(str(lineNumber)))
        colon = ':' if match else ' '
        
        return ' {sp}{lineNumber}{colon} {text}'.format(lineNumber = lineNumber,
                colon = colon, text = line, sp = spacer)


    def _append(self, view, edit, text, newline = True):
        view.insert(edit, view.size(), text)
        if newline:
            view.insert(edit, view.size(), '\n')
