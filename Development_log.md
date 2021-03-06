# 开发日志「Development log」
#####——himawari8-observer


&emsp;&emsp;这个项目目的其实就是我用来重新熟悉python环境的。现在毕业快一年了，但工作环境以嵌入式开发为主，用的是C语言。开发内容、开发设备环境都比较弱后，开发过程也比较无聊。于是在上班摸鱼的过程中就干脆重新拾起一些小项目玩一玩。
&emsp;&emsp;其实我一直想做的是桌面的应用开发，但桌面应用的开发我经常感觉受到很多限制，比如平台，工具，还有懒。对于桌面应用的开发其实我更应该选择C#或C++的一些项目来学习，但使用Visual Studio经常会遇到很多复杂的破问题。这样的学习过程让我感到十分烦躁。而我大学毕业设计使用的python成了我学习的第二阵地。
&emsp;&emsp;python经常会因为各种原因受到很多的争议。但从开发环境来说，python是让我觉得最舒服的。
&emsp;&emsp;至于为什么会写这个开发日志。这其实只是我在某天早上刷牙时的心血来潮而已。这种长篇的日志对开发工作其实并不算是高效的东西，但记录这个过程是很有趣的。我很喜欢记录自己内心的独白。这种思考过程不会有人感兴趣，但只要写出来就总会有人看。
&emsp;&emsp;说回himawari8-observer项目本身，这个项目其实本身是用来学习的。但从建项到现在开始开发日志已经过去了很长一段时间。这期间我已经解决了一些问题，并且是我之前完全不了解的问题。我尽量还原这期间遇到的问题，和解决思路。或许我的思路可能会很幼稚，也希望大家多多包涵和提出宝贵建议。
&emsp;&emsp;废话到这里就结束了。

>**2021-05-17**
>&emsp;&emsp;这是我建项的时间，索性时间也就先从这里开始。我是从[himawaripy——Set near-realtime picture of Earth as your desktop background](https://github.com/boramalper/himawaripy)看到的想法。而我是从[HelloGitHub——分享 GitHub 上有趣、入门级的开源项目](https://github.com/521xueweihan/HelloGitHub)发现的这个项目的。
>&emsp;&emsp;其实在建库之前我就已经开始准备这个项目的一些东西，例如怎么从himawari8的网站上获取他们的11000x11000像素的图片。
>&emsp;&emsp;显然，我首先遇到的就是如何下载，和如何使用python替换window10的桌面背景。下载其实有两个网址，[向日葵-8号实时网页](https://himawari8.nict.go.jp/)和[himawari8——NICT SCIENCE CLOUD](https://sc-nc-web.nict.go.jp/wsdb_osndisk/shareDirDownload/bDw2maKV)。前者只能下载550像素的照片，放到桌面上清晰度非常低；后者能直接下载11000x11000像素的照片，但用到了post请求和每次刷更换不同的hash值来创建下载，我无法直接获取下载。
>&emsp;&emsp;如何从himawari8直接获取post请求花了我半个月的时间，这期间我使用JavaScript和直接修改html来发送请求来尝试获取照片，但失败了。我认为是网站有防止爬机制，因此我伪造了post请求的head数据，但也失败了。我重新寻找问题所在，由于在发送几次post请求后，在post请求的data数据中Token的hash值就会改变，我认为是由于hash值的改变导致了请求失效。我从原网址的html中获取hash值，再到其他随便什么网站发送post请求，居然成功了。我成功迈出了这一步，我感到无比兴奋。但遗憾的是这通常只能下载几次，在这之后下载请求就会404失效。我依旧没有稳定的下载途径，因为我每次从原网址获取不同的hash值。并且我在python上发送post请求永远都是404。这让我非常苦恼。
>&emsp;&emsp;这问题困扰了我一段时间之后，我发现了另一个himawari8的github项目——[HimawariDownloader](https://github.com/LsHallo/HimawariDownloader)。这是个java项目，但它给我提供了一个全新的获取高像素照片的方法——合成。
>&emsp;&emsp;我在前面提到的[向日葵-8号实时网页](https://himawari8.nict.go.jp/)，其实里面的图片很容易获取下载的url，但只有550像素。但在网页放大图片的过程中它会放大地球照片，在这个过程中它并不是放大低像素的照片，这样会导致像素更低。而是选择高像素的照片切分成多张550像素的照片。而只要我们反向操作，把这些550像素的照片重新合成一张图片，不久变成一张高像素的照片了么。而下载照片——合成照片——替换桌面的简单思路就形成了。

>**2021-05-20**
>&emsp;&emsp;自从上次有了思路后，开始着手写程序。我需要几个主要功能，一个是下载全部的图片、一个是合成图片、一个是替换桌面；但我还想要一些其他功能，我希望能选择图片的清晰度、使用命令行参数来控制程序，还可以在其他平台上使用。
>&emsp;&emsp;下载图片还算轻松，根据日期和发送不同的url就可以获取。但我在家中的网络中下载，400张图片需要20多分钟，这远超过卫星实时网页发送最新照片的时间。这需要一个解决方法，例如线程，但我决定先把这个问题放一放。
>&emsp;&emsp;第二个功能，我需要把这些照片全部合成，这并不是原生库能做到的事情了。原本我希望不适用原生环境，但我还是太嫩了。迫不得已使用了PIL的Image库来将下载的图片合成一张（如果是11000x11000像素的照片下载下来一共有400张图片）。这个过程也不算太难，在简单尝试之后也顺利完成了。但我比较担心内存占用问题，毕竟一张高像素图片需要占用几百M的空间。我没有好的方法来测试，因此这问题也只能先放一放。
>&emsp;&emsp;第三步，替换桌面。这里简单调用win32gui中的方法就行。问题在于这里的方法其实本身并不稳定，说不定哪天这个接口就改了。而且我对其会照成什么影响也不知道，只知道它替换了桌面。这可能就是因为大家都更喜欢开源的原因。因为接口的实现如果是封闭的，你不知道使用它后会照成什么样的后果。
>&emsp;&emsp;至此，三大主要功能就完成了。虽然无法直接获取高像素照片心有不甘，但也算小有所成。还是非常开心的。

>**2021-06-08**
>&emsp;&emsp;这段时间了趟差，真是太累了。还顺便通关了《巫师三》的两个DLC，血与酒的DLC真是太棒了。
>&emsp;&emsp;在这天，我重新尝试使用python来发送post请求，想从[himawari8——NICT SCIENCE CLOUD](https://sc-nc-web.nict.go.jp/wsdb_osndisk/shareDirDownload/bDw2maKV)直接获取照片，但依旧失败。我意识到我在python上同样是伪造post请求，但我依旧需要每次都从网页赋值新的hash值。会不会是因为请求的hash值在我通过程序发送请求的时候改变了，导致无法通过，最终只能无奈404。如果想让请求的hash值和请求的内容保持一致，那我需要获取当前请求的hash值。这又需要我无奈的使用新的第三方库。lxml库，解析html，获取当前请求的html元素的值。一顿操作，我可以得到当前请求的hash值了。并且发现，每次请求的hash值确实是不一样的。这跟我之前在网页中伪造post请求是不一样的，因为在网页中，同一个hash值有时候是可以重复多次下载的。但也验证了我的思路，下载请求的hash值确实是会因为每次的请求而变化的。而到这里我也才知道，原来它不是hash值，而是用户令牌Token值。是在不使用用户密码的情况下请求数据的。我甚至不需要什么post的请求头。只需要post的data就行了。最少，我成功了，我可以直接下载高像素图片，而不用下载400多张再进行合成了，重大突破。
>&emsp;&emsp;这里有个小插曲。在寻找下载的过程中，我根据得到的下载链接，沿着域名向上寻找发现了后台的登陆系统[NICT SCIENCE CLOUD](https://sc-nc-web.nict.go.jp/wsdb_osndisk)。这个NICT似乎指日本一个叫做情报通信机构的机构。我无法在这后台注册，找回（因为请求都是404），自然也无法登录。或许我有机会可以去尝试一下。

>**2021-06-10**
>&emsp;&emsp;没什么灵感的时间里我去搞了另外一个我一直想做的东西，那就是悬浮窗口。一般的悬浮窗口都是用修改样式实现的，功能上一般会一直置顶。而有些不置顶的窗口等级没有桌面高，会因为按到显示桌面而被隐藏掉。因此我就自己做了一个显示桌面的tkinter的窗口。[tkinter_floating_window——A Tkinter window that will not be killed by the display desktop](https://github.com/zhengqingquan/tkinter_floating_window)

>**2021-06-22**
>&emsp;&emsp;下载任务就绪后，我开始着手去改善用户体验了。命令行其实之前也搞过，但稍微有些复杂。我想做的功能是不希望程序在输入错误的命令行后退出，而是给出提示，让用户继续输入。毕竟我想做的这个程序其实是个桌面应用。我在这里用到的命令行库是argparse。这是python官方支持的，似乎使用的也挺多的。在这期间，我从另外几个项目也得到一些灵感，比如[tomato-clock](https://github.com/coolcode/tomato-clock)和[alive-progress](https://github.com/rsalmei/alive-progress)，这两个都可以让我实现下载的进度条的功能和使用ctrl+c的方法退出程序。前者甚至只有百来行代码。
>&emsp;&emsp;说回命令行，这其实是让我非常头痛的东西。因为用户的交互不符合我的预期。如果用户参数有问题会自动结束程序，而如果输入正常，例如-h，也会自动结束程序——在不熟悉程序的情况下，如果我想输入一条命令行我需要每次都输入-h来查看程序拥有的功能。更糟糕的是，如果使用了命令行会导致应用层和用户输入层杂糅在一起，让主程序的代码看起来非常的丑陋。还有一个重要的情况是，如果用户只输入一个参数，其他几个参数会使用默认值。这会导致，在不知道的情况下，更改了其他几个参数值。这也严重不符合我的预期。
>&emsp;&emsp;命令行的退出是以抛出SystemExit错误结束的，我只能捕获这个错误，让程序进入我想要的循环中。除了提供-o（out）命令来让程序退出，还需要其他命令来控制下载的像素和下载方式——因为我们找到了post请求的下载方式，现在可以使用合成的方法还有发送post请求直接下载的方式。我称之为「碎片下载方式」和「完整下载方式」。
>&emsp;&emsp;这段时间发现个不错的乐队，黑屋乐队——我们经历风雨却害怕平庸。

>**2021-06-23**
>&emsp;&emsp;接下来的计划可能会比较困难，我需要让程序不断的运行。例如用户输入正确的命令行后程序可以自己完成一系列工作，而用户可以随时打断程序的运行——例如暂停下载。这肯定是需要用到线程了。我还需要更下载的进度条，提高交互的观赏性。如果只是下载一张图片这可能比较简单，但对于400张图片可能输出并不一定那么好看。这我之前也尝试过，但总有些小毛病。有时候下载也会莫名其妙的中断，可能是我网络卡了之类的，需要设置一个重置的时间。
>&emsp;&emsp;我还想写一个记录日志的功能，这样就不用每次都使用print打印乱七八糟的东西了。还有一个是相对路径和绝对路径的问题，这个也是我觉得比较头疼的地方，这对我测试不同的模块会有很大的麻烦。因为不同的模块对一个相对路径是不一样的。