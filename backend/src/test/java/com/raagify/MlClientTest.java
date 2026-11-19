package com.raagify;

import com.sun.net.httpserver.HttpServer;
import java.net.InetSocketAddress;
import java.nio.file.Files;
import java.util.concurrent.Executors;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class MlClientTest {
    @Test void realHttpReadTimeoutAndServiceDownReturnUnavailable() throws Exception {
        var server=HttpServer.create(new InetSocketAddress("127.0.0.1",0),0);
        var executor=Executors.newCachedThreadPool();server.setExecutor(executor);
        server.createContext("/analyze-file",exchange->{try{Thread.sleep(600);exchange.sendResponseHeaders(200,0);exchange.close();}catch(Exception ignored){}});server.start();
        var file=Files.createTempFile("raagify-test-",".wav");Files.write(file,new byte[]{1,2,3});
        try {
            var client=new MlClient("http://127.0.0.1:"+server.getAddress().getPort(),100,80);
            long start=System.nanoTime();assertFalse(client.analyze(file).available());assertTrue((System.nanoTime()-start)/1e6<1500);
            int port=server.getAddress().getPort();server.stop(0);assertFalse(new MlClient("http://127.0.0.1:"+port,100,100).analyze(file).available());
        } finally {server.stop(0);executor.shutdownNow();Files.deleteIfExists(file);}
    }
    @Test void cosineRanksIdenticalVectorsAndHandlesZeros() {
        assertEquals(1,Recommendations.cosine(java.util.List.of(1.0,2.0),java.util.List.of(1.0,2.0)),1e-9);
        assertEquals(0,Recommendations.cosine(java.util.List.of(0.0,0.0),java.util.List.of(1.0,2.0)));
    }
}
