project('test_package', 'c')
xaw = dependency('xaw7', required : false)
if not xaw.found()
  xaw = dependency('xaw6')
endif
executable('test_package',
            sources : ['test_package.c'],
            dependencies : [xaw])
