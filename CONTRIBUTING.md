# Contributor's Guide

We're building security-critical enterprise software that is in production 
use by multiple companies. Some network devices do not allow for read-only 
access, so there will be some environments where ConfigMaster has partial 
read-write access to core networking infrastructure. Keep this in mind while 
you're working on the code!

This implies an emphasis on secure, well-written, tested and reliable code. 
Quality is preferred over quantity. 

## Releases

For now, there's exactly one supported release - the master branch. It must 
be production ready at all times. All changes need to be backwards compatible.

Formal releases will be introduced as the project grows, but aren't necessary
for now.

## Review Workflow

The master branch is protected and the only way to get code into it is to 
open a pull request.

Nobody has permissions to directly commit to the master, including the 
project administrators. This ensures that every single change is reviewed.

## Branching

*Every master commit = one idea.* 

Keep master commits as self-contained as possible. Each commit should contain
one logical change/idea. Squash checkpoint commits.

A merge request may contain multiple commits as long as they are related and
it makes sense to review them together. Split commits into multiple PRs if
they are unrelated.

To be decided: merge vs. rebase

We want to avoid long-lived feature branches and get changes reviewed as soon
as possible, so many self-contained small PRs are better than large, infrequent
PRs that contain a large number of changes at once.

The Phabricator book has a nice explanation of this workflow [2] (we're not 
using Phabricator, but our development workflow is heavily inspired from 
theirs).

## Coding Style

We're following PEP-8 and the Google Python Style guide [1]. We try to follow
the 79-character line limit (configure your IDE!) except when it makes the 
code obviously less readable.

As soon as the project has been moved over to Python 3, the entire code base 
will have type annotations added.
 
Any exceptions will be documented here.

## TODO comments

Sometimes, you need to write code that introduces technical debt. Obviously,
this is best avoided, but there are some situations where you cannot avoid
a quick hack.

In order to make sure that whatever atrocity you introduced will be cleaned up
later and to increase the chance for your changes to make it through code 
review, add a "TODO" comment.

## Documentation

Both code and user documentation is automatically generated from the 
repository using Sphinx. Sphinx understands the Google docstring format using
the Napoleon extension [3]. Sphinx uses the ReST markup format, which is 
light-weight markup format similar to Markdown, but specifically geared 
torwards technical documentation [4].

For development, there's an auto-reloading doc server:

    ./docserver.sh
    
Internal API docs are generated from the docstrings using the autodoc 
extension. You need to run `./apidocs.sh` to generate the skeleton.
Re-run the script if you add or remove modules.

A webhook automatically triggers a rebuild of the official documentation on 
each merge into master.

[1]: https://google.github.io/styleguide/pyguide.html
[2]: https://secure.phabricator.com/book/phabflavor/article/recommendations_on_revision_control/#one-idea-is-one-commit
[3]: http://www.sphinx-doc.org/en/stable/ext/napoleon.html
[4]: http://www.sphinx-doc.org/en/stable/rest.html