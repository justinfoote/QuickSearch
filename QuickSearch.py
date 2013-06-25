from collections import defaultdict
import os
import re

import sublime
import sublime_plugin


class FindInFileCommand(sublime_plugin.TextCommand):
    """A first attempt at find all in the current file
    """

    def run(self, *args):
        self.resultsPane = self._getResultsPane()
        if self.resultsPane is None:
            return False

        self._callbackWithWordToFind(self._doFind)


    def _callbackWithWordToFind(self, callback):
        if len(self.view.sel()) == 1 and self.view.sel()[0].size() > 0:
            callback(self.view.substr(self.view.sel()[0]))
        else:
            self.view.window().show_input_panel('Enter word to find:', '', 
                    callback, None, None)


    def _doFind(self, wordToFind):
        toFind = re.escape(wordToFind)
        regions = self.view.find_all(toFind)
        lines = defaultdict(list)
        for r in regions:
            line = self.view.rowcol(r.begin())[0]
            lines[line] += [r]
            for i in range(max(0, line - 2), min(self._lineCount(), line + 3)):
                # merely addressing the lines will ensure they are included
                # in the output
                lines[i]

        toAppend = [self.view.file_name() + ":"]
        lastLine = None
        for lineNumber in sorted(lines):
            if lastLine and lineNumber > lastLine + 1:
                toAppend.append(' ' * (5 - len(str(lineNumber)))
                        + '.' * len(str(lineNumber)))
            lastLine = lineNumber

            lineText = self.view.substr(self.view.line(
                    self.view.text_point(lineNumber, 0)))
            
            toAppend.append(self._format('%s' % (lineNumber + 1),
                    lineText, bool(lines[lineNumber])))

        self.resultsPane.run_command('show_quick_search_results',
                {'toAppend': toAppend, 'toHighlight': toFind})


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
        return v


    def _format(self, lineNumber, line, match = False):
        spacer = ' ' * (4 - len(str(lineNumber)))
        colon = ':' if match else ' '
        
        return ' {sp}{lineNumber}{colon} {text}'.format(lineNumber = lineNumber,
                colon = colon, text = line, sp = spacer)


    def _lineCount(self):
        return self.view.rowcol(self.view.size())[0]


class ShowQuickSearchResultsCommand(sublime_plugin.TextCommand):
    def run(self, edit, toAppend, toHighlight):
        self.view.erase(edit, sublime.Region(0, self.view.size()))
        self.view.insert(edit, self.view.size(), '\n'.join(toAppend))

        regions = self.view.find_all(toHighlight)
        self.view.add_regions('find_results', regions, 'found', '', 
                sublime.DRAW_OUTLINED)