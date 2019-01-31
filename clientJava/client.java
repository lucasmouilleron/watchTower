import javax.net.ssl.*;
import java.io.BufferedReader;
import java.io.DataOutputStream;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.security.KeyManagementException;
import java.security.KeyStoreException;
import java.security.NoSuchAlgorithmException;
import java.security.cert.CertificateException;
import java.security.cert.X509Certificate;

public class client
{
    /////////////////////////////////////////////////////////////////////////////////////////
    private static final int TIMEOUT_IN_MSECS = 10 * 1000;
    /////////////////////////////////////////////////////////////////////////////////////////
    public int port = 0;
    public String url = "";
    public String password = "";
    public boolean allowUnsecureHttps = false;

    /////////////////////////////////////////////////////////////////////////////////////////
    public client(String url, int port, String password, boolean allowUnsecureHttps)
    {
        this.url = url;
        this.port = port;
        this.password = password;
        this.allowUnsecureHttps = allowUnsecureHttps;
    }

    /////////////////////////////////////////////////////////////////////////////////////////
    public String pulse(String service, String alertType, String alertTarget, int nextIn) throws Exception
    {
        HttpURLConnection connection = (HttpURLConnection) new URL(this.url + ":" + this.port + "/heartbeat").openConnection();
        if(allowUnsecureHttps)
        {
            TrustModifier.relaxHostChecking(connection);
        }
        connection.addRequestProperty("password", this.password);
        connection.addRequestProperty("content-type", "application/json");
        connection.setRequestMethod("POST");
        connection.setDoOutput(true);
        writeDatas(String.format("{\"service\":\"%s\",\"alertType\":\"%s\",\"alertTarget\":\"%s\",\"nextIn\":%d}", service, alertType, alertTarget, nextIn), connection);
        return readAllContent(connection);
    }

    /////////////////////////////////////////////////////////////////////////////////////////
    public String cancel(String service) throws Exception
    {
        HttpURLConnection connection = (HttpURLConnection) new URL(this.url + ":" + this.port + "/heartbeat").openConnection();
        if(allowUnsecureHttps)
        {
            TrustModifier.relaxHostChecking(connection);
        }
        connection.addRequestProperty("password", this.password);
        connection.addRequestProperty("content-type", "application/json");
        connection.setRequestMethod("DELETE");
        connection.setDoOutput(true);
        writeDatas(String.format("{\"service\":\"%s\"}", service), connection);
        return readAllContent(connection);
    }

    /////////////////////////////////////////////////////////////////////////////////////////
    private String doSendEvent(String service, String message, int level) throws Exception
    {
        try
        {
            HttpURLConnection connection = (HttpURLConnection) new URL(this.url + ":" + this.port + "/event").openConnection();

            if(allowUnsecureHttps)
            {
                TrustModifier.relaxHostChecking(connection);
            }

            connection.addRequestProperty("password", this.password);
            connection.addRequestProperty("content-type", "application/json");
            connection.setRequestMethod("POST");
            connection.setDoOutput(true);
            writeDatas(String.format("{\"service\":\"%s\",\"message\":\"%s\",\"level\":\"%s\"}", service, cleanupField(message), level), connection);
            return readAllContent(connection);
        }
        catch(Exception e)
        {
            e.printStackTrace();
            return "";
        }
    }

    /////////////////////////////////////////////////////////////////////////////////////////
    public String add(final String service, final String message, int level, boolean inThread) throws Exception
    {
        if(!inThread)
        {
            return this.doSendEvent(service, message, level);
        }
        else
        {
            new sendEventThread(this, service, message, level).start();
            return "async launched";
        }
    }

    /////////////////////////////////////////////////////////////////////////////////////////
    private class sendEventThread extends Thread
    {
        client client;
        String service;
        String message;
        int level;

        public sendEventThread(client client, String service, String message, int level)
        {
            this.client = client;
            this.service = service;
            this.message = message;
            this.level = level;
        }

        public void run()
        {
            try
            {
                this.client.doSendEvent(this.service, this.message, this.level);
            }
            catch(Exception e) { }
        }
    }

    /////////////////////////////////////////////////////////////////////////////////////////
    private void writeDatas(String postDataString, HttpURLConnection connection) throws Exception
    {
        byte[] postData = postDataString.getBytes(StandardCharsets.UTF_8);
        connection.setRequestProperty("Content-Length", Integer.toString(postData.length));
        connection.setConnectTimeout(TIMEOUT_IN_MSECS);
        connection.setReadTimeout(TIMEOUT_IN_MSECS);
        new DataOutputStream(connection.getOutputStream()).write(postData);
    }

    /////////////////////////////////////////////////////////////////////////////////////////
    private String readAllContent(HttpURLConnection connection) throws Exception
    {
        connection.setConnectTimeout(TIMEOUT_IN_MSECS);
        connection.setReadTimeout(TIMEOUT_IN_MSECS);
        BufferedReader reader = new BufferedReader(new InputStreamReader(connection.getInputStream(), StandardCharsets.UTF_8));
        String content = "";
        String line;
        while((line = reader.readLine()) != null)
        {
            content = line + "\n";
        }
        return content;
    }

    /////////////////////////////////////////////////////////////////////////////////////////
    private String cleanupField(String field)
    {
        return field.replaceAll("\"", "\\\\\"").replaceAll("\\p{C}", " ").replaceAll("\\s{2,}", " ").trim();
    }
}

/////////////////////////////////////////////////////////////////////////////////////////
class TrustModifier
{
    private static final TrustingHostnameVerifier TRUSTING_HOSTNAME_VERIFIER = new TrustingHostnameVerifier();
    private static SSLSocketFactory factory;

    public static void relaxHostChecking(HttpURLConnection conn) throws KeyManagementException, NoSuchAlgorithmException, KeyStoreException
    {

        if(conn instanceof HttpsURLConnection)
        {
            HttpsURLConnection httpsConnection = (HttpsURLConnection) conn;
            SSLSocketFactory factory = prepFactory(httpsConnection);
            httpsConnection.setSSLSocketFactory(factory);
            httpsConnection.setHostnameVerifier(TRUSTING_HOSTNAME_VERIFIER);
        }
    }

    static synchronized SSLSocketFactory prepFactory(HttpsURLConnection httpsConnection) throws NoSuchAlgorithmException, KeyStoreException, KeyManagementException
    {

        if(factory == null)
        {
            SSLContext ctx = SSLContext.getInstance("TLS");
            ctx.init(null, new TrustManager[]{new AlwaysTrustManager()}, null);
            factory = ctx.getSocketFactory();
        }
        return factory;
    }

    private static final class TrustingHostnameVerifier implements HostnameVerifier
    {
        public boolean verify(String hostname, SSLSession session)
        {
            return true;
        }
    }

    private static class AlwaysTrustManager implements X509TrustManager
    {
        public void checkClientTrusted(X509Certificate[] arg0, String arg1) throws CertificateException
        {
        }

        public void checkServerTrusted(X509Certificate[] arg0, String arg1) throws CertificateException
        {
        }

        public X509Certificate[] getAcceptedIssuers()
        {
            return null;
        }
    }
}
