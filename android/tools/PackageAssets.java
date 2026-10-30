import java.io.InputStream;
import java.io.OutputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardCopyOption;
import java.util.Enumeration;
import java.util.zip.ZipEntry;
import java.util.zip.ZipFile;
import java.util.zip.ZipOutputStream;
import java.util.stream.Stream;

/** Add generated DEX and local content while preserving stored Android resources. */
public final class PackageAssets {
    private static void copy(InputStream from, OutputStream to) throws Exception {
        byte[] buffer = new byte[32768]; int count;
        while ((count = from.read(buffer)) != -1) to.write(buffer, 0, count);
    }
    private static void file(ZipOutputStream out, Path source, String name) throws Exception {
        out.putNextEntry(new ZipEntry(name));
        try (InputStream in = Files.newInputStream(source)) { copy(in, out); }
        out.closeEntry();
    }
    public static void main(String[] args) throws Exception {
        Path original = Paths.get(args[0]), temp = original.resolveSibling("packaged.apk");
        Path assets = Paths.get(args[2]);
        try (ZipFile source = new ZipFile(original.toFile()); ZipOutputStream out = new ZipOutputStream(Files.newOutputStream(temp))) {
            Enumeration<? extends ZipEntry> entries = source.entries();
            while (entries.hasMoreElements()) {
                ZipEntry old = entries.nextElement(), entry = new ZipEntry(old.getName());
                if (old.getMethod() == ZipEntry.STORED) { entry.setMethod(ZipEntry.STORED); entry.setSize(old.getSize()); entry.setCrc(old.getCrc()); }
                out.putNextEntry(entry);
                try (InputStream in = source.getInputStream(old)) { copy(in, out); }
                out.closeEntry();
            }
            file(out, Paths.get(args[1]), "classes.dex");
            try (Stream<Path> stream = Files.walk(assets)) {
                for (Path path : (Iterable<Path>) stream.filter(Files::isRegularFile)::iterator) {
                    file(out, path, "assets/" + assets.relativize(path).toString().replace('\\', '/'));
                }
            }
        }
        Files.move(temp, original, StandardCopyOption.REPLACE_EXISTING);
    }
}
