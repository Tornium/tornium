# Tornium Documentation
Tornium uses [Read The Docs](https://about.readthedocs.com/) for its documentation which uses [Sphinx](https://www.sphinx-doc.org/en/master/) and [reStructuredText](https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html) internally. You can view the hosted version of Tornium's documentation at [https://docs.tornium.com](https://docs.tornium.com). See below for instructions on how to contribute to Tornium.

> [!WARNING]
> The below instructions currently only work in Linux and MacOS, but the commands and steps can be adapted for Windows.

## Setting up the documentation locally
1. Install [Python](https://wiki.python.org/moin/BeginnersGuide/Download)
2. Install [git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)
3. Install a development environment:
    A development environment is an application where you can write and test code, debug applications, etc. This is a non-exhaustive lists of possible developer environments, the choice is mostly personal preference.

    - [Neovim](https://neovim.io/)
    - [VSCode](https://code.visualstudio.com/)
    - [Emacs](https://www.gnu.org/software/emacs/)
    - [Jetbrains PyCharm](https://www.jetbrains.com/pycharm/)
    - [Zed](https://zed.dev/)
4. Fork Tornium on GitHub.
5. Clone [Tornium](https://github.com/Tornium/tornium):
    ```bash
    git clone https://github.com/Tornium/tornium.git
    ```
6. Create Python virtual environment:
    ```bash
    cd tornium
    python3 -m venv venv
    source venv/bin/activate
    ```
7. Install documentation dependencies
    ```bash
    cd docs
    pip3 install -r requirements.txt
    ```
8. Create a branch for your changes:
    ```bash
    git checkout -b docs/update-docs-foo-bar
    ```
9. Make changes to documentation
10. "Build" documentation to HTML page:
    ```bash
    make html
    ```
11. Open generated documentation in a browser:
    ```bash
    Windows: start build/html/index.html
    Linux: xdg-open build/html/index.html
    MacOS: open build/html/index.html
    ```
12. Push your changes upstream:
    ```bash
    git add [[ changed-files ]]
    git commit -m "[docs] Improved foo bar"
    git push origin docs/update-docs-foo-bar
    ```
13. On Tornium's GitHub page, [create a Pull Request](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/creating-a-pull-request) for the change to be merged with the project.

## Contributing documentation
The [Sphinx](https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html) is a great resource for learning how to use reStructuredText in the documenation.

### What can be improved
Before contributing, take some time to familiarize yourself with the project, especially its current documentation. Look for areas where improvements can be made:
- Outdated information
- Spelling or grammar issues
- Missing guides, tutorials, or examples
- Hard-to-follow instructions or ambiguous content

### Guidelines on writing documentation
Adapted from Adam Scott's guide [^1]...

1. Write documentation that is inviting and clear
2. Write documentation that is comprehensive and details all aspects of Tornium
3. Write documentation that is skimmable
4. Write documentation that offers examples of how to use Tornium
5. Write documentation that has repetition, when useful
6. Write documentation that is up-to-date
7. Write documentation that is easy to contribute to
8. Write documentation that is easy to find

[Write the Docs](https://www.writethedocs.org/guide/writing/docs-principles/) provides a great, in-depth guide on writing high quality documentation if you're interested.


[^1]: [The eight rules of good documentation](https://www.oreilly.com/content/the-eight-rules-of-good-documentation/)
