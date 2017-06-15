from django.apps import AppConfig


class GitmateCodeAnalysisConfig(AppConfig):
    name = 'gitmate_code_analysis'
    verbose_name = 'Code Analysis'
    description = 'Checks new and updated pull requests of this repository '\
                  'for errors and bad practices. Issues introduced by the '\
                  'pull request in question will be commented on directly. '\
                  'The analysis uses <a href="https://coala.io">coala</a> '\
                  'and <b> needs to be configured via a file named '\
                  '<code>.coafile</code> in your repository, as described '\
                  '<a href="https://docs.coala.io/en/latest/Users/'\
                  'Tutorial.html">here<a/></b>.'
