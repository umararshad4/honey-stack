import http from 'node:http';

http.createServer((req, res) => {
  res.setHeader('Content-Type', 'text/html');
  if (req.url === '/empty') { res.end('<h1>No tools</h1>'); return; }
  res.end(`<!doctype html><h1>WebMCP counter</h1>
    <button>Increment</button><output role="status">0</output>
    <script>
    let count = 0;
    const show = () => document.querySelector('output').textContent = String(count);
    document.querySelector('button').onclick = () => { ${process.env.BROKEN_UI === '1' ? '' : 'count++; show();'} };
    const context = document.modelContext ?? navigator.modelContext;
    if (context) {
      context.registerTool({ name: 'increment', description: 'Increment the counter',
        inputSchema: { type: 'object', properties: { amount: { type: 'integer', minimum: 1 } }, required: ['amount'] },
        execute: ({amount}) => {
          if (!Number.isInteger(amount) || amount < 1) return {isError:true, content:[{type:'text',text:'Invalid amount'}]};
          count += amount; show(); return {content:[{type:'text',text:String(count)}]};
        }
      });
      context.registerTool({ name: 'failure', description: 'Return an error',
        execute: () => ({isError:true, content:[{type:'text',text:'Deliberate failure'}]}) });
      context.registerTool({ name: 'throws', description: 'Throw an error',
        execute: () => { throw new Error('Deliberate exception'); } });
      context.registerTool({ name: 'navigate', description: 'Change fixture route',
        execute: () => { history.pushState(null, '', '/changed'); return {content:[]}; } });
    }
    </script>`);
}).listen(Number(process.argv[2]), '127.0.0.1');
