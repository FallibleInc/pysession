### Pysession

Automatically save python interpreter code to a file or secret Gist. You can turn this off for any session. Helpful when you want to share a piece of code you just hacked on the shell or wanted to save it in a file for use later.

#### Installation steps

``` bash
pip install pysession
echo 'export PYTHONSTARTUP=$HOME/.pysession/pysession.py' >> ~/.bashrc
```

If you are using zsh replace `.bashrc` in the above line with `.zshrc` and similarly for any other shell.

#### How to use

By default, Pysession will record each shell run and save to a Gist. However it can be instructed to turn off recording or save to a file locally instead of GitHub.

##### To turn off saving for a session

``` python
>>> PySession.off()
```

##### To save to a local file instead of Gist

``` python
>>> PySession.local()
```
