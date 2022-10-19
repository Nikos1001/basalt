
cionom-cli.out --emit-bytecode=main.ibc main.cio
cionom-cli.out --emit-bytecode=test.ibc test.cio
cionom-cli.out --bundle=exe.cbe main.ibc test.ibc
cionom-cli.out --execute-bundle exe.cbe 
