using System.Diagnostics;
using System.Numerics;
using Raylib_cs;

// =========================================================
// ARCHITECTURE: CORE MATH & STRUCTURES
// =========================================================

public struct Ray
{
    public Vector3 Origin;
    public Vector3 Direction;

    public Ray(Vector3 origin, Vector3 direction)
    {
        Origin = origin;
        Direction = Vector3.Normalize(direction);
    }
}

public struct HitInfo
{
    public bool DidHit;
    public float Distance;
    public Vector3 Point;
    public Vector3 Normal;
    public Material Mat;
}

public struct Material
{
    public Vector3 Albedo;       // Base color (0.0 - 1.0)
    public float Specular;       // Specular coefficient (0.0 - 1.0)
    public float Smoothness;     // Shininess exponent
    public float Reflectivity;   // 0.0 - 1.0 (Mirror)
    public float Transparency;   // 0.0 - 1.0 (Glass)
    public float IOR;            // Index of Refraction (e.g., 1.5 for glass)

    public static Material Lambert(Vector3 color) => new() { Albedo = color, Specular = 0.0f, IOR = 1.0f };
    public static Material Metal(Vector3 color, float fuzz) => new() { Albedo = color, Specular = 1.0f, Smoothness = 50f, Reflectivity = 1.0f - fuzz, IOR = 1.0f };
    public static Material Glass(float ior) => new() { Albedo = Vector3.One, Specular = 1.0f, Smoothness = 100f, Reflectivity = 0.1f, Transparency = 0.9f, IOR = ior };
}

// =========================================================
// ARCHITECTURE: SCENE OBJECTS
// =========================================================

public abstract class SceneObject
{
    public Vector3 Position;
    public Material Mat;

    public abstract bool Intersect(Ray ray, out HitInfo hit);
}

public class Sphere : SceneObject
{
    public float Radius;

    public override bool Intersect(Ray ray, out HitInfo hit)
    {
        hit = new HitInfo();
        Vector3 oc = ray.Origin - Position;
        float a = Vector3.Dot(ray.Direction, ray.Direction);
        float b = 2.0f * Vector3.Dot(oc, ray.Direction);
        float c = Vector3.Dot(oc, oc) - Radius * Radius;
        float discriminant = b * b - 4 * a * c;

        if (discriminant < 0) return false;

        float dist = (-b - MathF.Sqrt(discriminant)) / (2.0f * a);
        if (dist < 0.001f) // Try second root if inside
            dist = (-b + MathF.Sqrt(discriminant)) / (2.0f * a);

        if (dist < 0.001f) return false;

        hit.DidHit = true;
        hit.Distance = dist;
        hit.Point = ray.Origin + ray.Direction * dist;
        hit.Normal = Vector3.Normalize(hit.Point - Position);
        hit.Mat = Mat;
        return true;
    }
}

public class Cube : SceneObject
{
    public Vector3 Size; // Half-extents (from center)

    public override bool Intersect(Ray ray, out HitInfo hit)
    {
        hit = new HitInfo();

        Vector3 min = Position - Size;
        Vector3 max = Position + Size;

        // --- FIX: Безопасное вычисление обратного направления ---
        // Если компонент направления луча близок к 0, используем огромное число вместо деления на 0.
        // Это предотвращает появление NaN (0/0) и Infinity, которые ломают логику.
        float invDirX = MathF.Abs(ray.Direction.X) < 1e-6f ? 1e20f : 1.0f / ray.Direction.X;
        float invDirY = MathF.Abs(ray.Direction.Y) < 1e-6f ? 1e20f : 1.0f / ray.Direction.Y;
        float invDirZ = MathF.Abs(ray.Direction.Z) < 1e-6f ? 1e20f : 1.0f / ray.Direction.Z;

        float tMinX = (min.X - ray.Origin.X) * invDirX;
        float tMaxX = (max.X - ray.Origin.X) * invDirX;
        float tMin = MathF.Min(tMinX, tMaxX);
        float tMax = MathF.Max(tMinX, tMaxX);

        float tMinY = (min.Y - ray.Origin.Y) * invDirY;
        float tMaxY = (max.Y - ray.Origin.Y) * invDirY;
        tMin = MathF.Max(tMin, MathF.Min(tMinY, tMaxY));
        tMax = MathF.Min(tMax, MathF.Max(tMinY, tMaxY));

        float tMinZ = (min.Z - ray.Origin.Z) * invDirZ;
        float tMaxZ = (max.Z - ray.Origin.Z) * invDirZ;
        tMin = MathF.Max(tMin, MathF.Min(tMinZ, tMaxZ));
        tMax = MathF.Min(tMax, MathF.Max(tMinZ, tMaxZ));

        // Если нет пересечения
        if (tMax < tMin || tMax < 0) return false;

        float finalDist = tMin > 0.001f ? tMin : tMax;

        // --- FIX: Дополнительная проверка на NaN перед использованием ---
        if (finalDist < 0.001f || float.IsNaN(finalDist)) return false;

        hit.DidHit = true;
        hit.Distance = finalDist;
        hit.Point = ray.Origin + ray.Direction * finalDist;
        hit.Mat = Mat;

        // --- FIX: Расчет нормали ---
        // Вычисляем нормаль, находя ось с максимальным проникновением
        Vector3 p = hit.Point - Position;
        // Делим на размер, чтобы привести к нормализованному диапазону (-1..1)
        // Добавляем защиту от NaN в самом векторе p (хотя проверка finalDist должна была помочь)
        Vector3 d = new Vector3(
            MathF.Abs(p.X) / Size.X,
            MathF.Abs(p.Y) / Size.Y,
            MathF.Abs(p.Z) / Size.Z
        );

        Vector3 normal = Vector3.Zero;

        // Используем SafeSign вместо MathF.Sign, чтобы гарантировать отсутствие краша
        if (d.X > d.Y && d.X > d.Z) normal = new Vector3(SafeSign(p.X), 0, 0);
        else if (d.Y > d.Z) normal = new Vector3(0, SafeSign(p.Y), 0);
        else normal = new Vector3(0, 0, SafeSign(p.Z));

        hit.Normal = Vector3.Normalize(normal);

        return true;
    }

    // Вспомогательный метод, который никогда не падает
    private float SafeSign(float value)
    {
        if (float.IsNaN(value)) return 0;
        return value >= 0 ? 1.0f : -1.0f;
    }
}

// =========================================================
// ENGINE: RAY TRACER
// =========================================================

public class RayTracer
{
    private List<SceneObject> _objects = new();
    private Vector3 _lightPos = new Vector3(0, 1.8f, 0);
    private Vector3 _lightColor = new Vector3(1.0f, 1.0f, 1.0f);
    private float _lightIntensity = 1.5f;

    // References to modify scene from input
    public SceneObject? CentralObject;
    public SceneObject? BackWall;

    public void InitScene()
    {
        _objects.Clear();

        // --- Cornell Box Walls (Constructed from flattened Cubes) ---
        float roomSize = 2.0f;
        float wallThickness = 0.1f;

        // Floor (White)
        _objects.Add(new Cube { Position = new Vector3(0, -roomSize - wallThickness, 0), Size = new Vector3(roomSize, wallThickness, roomSize), Mat = Material.Lambert(new Vector3(1.0f)) });
        // Ceiling (White)
        _objects.Add(new Cube { Position = new Vector3(0, roomSize + wallThickness, 0), Size = new Vector3(roomSize, wallThickness, roomSize), Mat = Material.Lambert(new Vector3(1.0f)) });
        // Back Wall (White) - user modifiable
        BackWall = new Cube { Position = new Vector3(0, 0, roomSize + wallThickness), Size = new Vector3(roomSize, roomSize, wallThickness), Mat = Material.Lambert(new Vector3(1.0f)) };
        _objects.Add(BackWall);

        // Left Wall (Red)
        _objects.Add(new Cube { Position = new Vector3(-roomSize - wallThickness, 0, 0), Size = new Vector3(wallThickness, roomSize, roomSize), Mat = Material.Lambert(new Vector3(1.0f, 0.2f, 0.2f)) });
        // Right Wall (Green)
        _objects.Add(new Cube { Position = new Vector3(roomSize + wallThickness, 0, 0), Size = new Vector3(wallThickness, roomSize, roomSize), Mat = Material.Lambert(new Vector3(0.2f, 1.0f, 0.2f)) });

        // --- Objects Inside ---

        // Central Sphere (The one we toggle)
        CentralObject = new Sphere { Position = new Vector3(0, -1.0f, -0.5f), Radius = 1.0f, Mat = Material.Lambert(new Vector3(0.2f, 0.5f, 0.9f)) };
        _objects.Add(CentralObject);

        // A small cube rotated (simulated by positioning for now as axis-aligned)
        _objects.Add(new Cube { Position = new Vector3(1.2f, -1.5f, 0.5f), Size = new Vector3(0.5f, 0.5f, 0.5f), Mat = Material.Metal(new Vector3(0.9f, 0.8f, 0.2f), 0.1f) });
    }

    public void UpdateInput()
    {
        // Light Movement
        float speed = 0.1f;
        if (Raylib.IsKeyDown(KeyboardKey.Left)) _lightPos.X -= speed;
        if (Raylib.IsKeyDown(KeyboardKey.Right)) _lightPos.X += speed;
        if (Raylib.IsKeyDown(KeyboardKey.Up)) _lightPos.Z -= speed; // Move deeper
        if (Raylib.IsKeyDown(KeyboardKey.Down)) _lightPos.Z += speed; // Move closer

        // Material Toggles
        if (Raylib.IsKeyPressed(KeyboardKey.M) && CentralObject != null)
        {
            // Toggle Mirror
            if (CentralObject.Mat.Reflectivity > 0.0f)
                CentralObject.Mat = Material.Lambert(new Vector3(0.2f, 0.5f, 0.9f));
            else
                CentralObject.Mat = Material.Metal(new Vector3(0.9f, 0.9f, 0.9f), 0.0f);
        }

        if (Raylib.IsKeyPressed(KeyboardKey.T) && CentralObject != null)
        {
            // Toggle Transparency
            if (CentralObject.Mat.Transparency > 0.0f)
                CentralObject.Mat = Material.Lambert(new Vector3(0.2f, 0.5f, 0.9f));
            else
                CentralObject.Mat = Material.Glass(1.5f);
        }

        if (Raylib.IsKeyPressed(KeyboardKey.W) && BackWall != null)
        {
             // Make back wall mirror
             BackWall.Mat = Material.Metal(new Vector3(0.9f), 0.05f);
        }

        if (Raylib.IsKeyPressed(KeyboardKey.Space))
        {
            // Add random sphere
            var rand = new Random();
            float r = (float)rand.NextDouble() * 0.4f + 0.1f;
            float x = (float)rand.NextDouble() * 2.0f - 1.0f;
            float y = (float)rand.NextDouble() * 2.0f - 1.0f;
            _objects.Add(new Sphere {
                Position = new Vector3(x, y, -0.5f),
                Radius = r,
                Mat = Material.Lambert(new Vector3((float)rand.NextDouble(), (float)rand.NextDouble(), (float)rand.NextDouble()))
            });
        }
    }

    // Main Ray Trace Logic
    public Vector3 Trace(Ray ray, int depth)
    {
        if (depth <= 0) return Vector3.Zero;

        if (!GetClosestHit(ray, out HitInfo hit, out _))
        {
            return Vector3.Zero; // Black background (closed room)
        }

        Vector3 finalColor = Vector3.Zero;

        // 1. Calculate Lighting (Phong Blinn)
        Vector3 viewDir = Vector3.Normalize(-ray.Direction);
        Vector3 lightDir = Vector3.Normalize(_lightPos - hit.Point);
        float distToLight = Vector3.Distance(_lightPos, hit.Point);

        // Shadow check
        bool inShadow = false;
        Ray shadowRay = new Ray(hit.Point + hit.Normal * 0.001f, lightDir);
        if (GetClosestHit(shadowRay, out HitInfo shadowHit, out _))
        {
            if (shadowHit.Distance < distToLight) inShadow = true;
        }

        if (!inShadow || hit.Mat.Transparency > 0) // Allow light through if object is glass-like
        {
            // Diffuse
            float NdotL = MathF.Max(0, Vector3.Dot(hit.Normal, lightDir));
            Vector3 diffuse = hit.Mat.Albedo * _lightColor * NdotL * _lightIntensity;

            // Specular
            Vector3 halfVector = Vector3.Normalize(lightDir + viewDir);
            float NdotH = MathF.Max(0, Vector3.Dot(hit.Normal, halfVector));
            float specFactor = MathF.Pow(NdotH, hit.Mat.Smoothness > 0 ? hit.Mat.Smoothness : 1.0f);
            Vector3 specular = _lightColor * hit.Mat.Specular * specFactor * _lightIntensity;

            finalColor += diffuse + specular;
        }

        // Ambient
        finalColor += hit.Mat.Albedo * 0.03f;

        // 2. Reflection
        if (hit.Mat.Reflectivity > 0.0f)
        {
            Vector3 reflectDir = Vector3.Reflect(ray.Direction, hit.Normal);
            Ray reflectRay = new Ray(hit.Point + hit.Normal * 0.001f, reflectDir);
            finalColor = Vector3.Lerp(finalColor, Trace(reflectRay, depth - 1), hit.Mat.Reflectivity);
        }

        // 3. Refraction (Transparency)
        if (hit.Mat.Transparency > 0.0f)
        {
            float eta = 1.0f / hit.Mat.IOR; // Assuming entering from air
            Vector3 normal = hit.Normal;

            // Check if we are inside the object (exiting)
            if (Vector3.Dot(ray.Direction, normal) > 0)
            {
                normal = -normal;
                eta = hit.Mat.IOR; // Exiting to air
            }

            Vector3 refractDir = Refract(ray.Direction, normal, eta);
            if (refractDir != Vector3.Zero)
            {
                Ray refractRay = new Ray(hit.Point - normal * 0.002f, refractDir); // bias inside
                Vector3 refractColor = Trace(refractRay, depth - 1);
                finalColor = Vector3.Lerp(finalColor, refractColor, hit.Mat.Transparency);
            }
        }

        return finalColor;
    }

    private bool GetClosestHit(Ray ray, out HitInfo bestHit, out SceneObject? hitObj)
    {
        bestHit = new HitInfo { Distance = float.MaxValue };
        hitObj = null;
        bool didHit = false;

        foreach (var obj in _objects)
        {
            if (obj.Intersect(ray, out HitInfo hit))
            {
                if (hit.Distance < bestHit.Distance)
                {
                    bestHit = hit;
                    hitObj = obj;
                    didHit = true;
                }
            }
        }
        return didHit;
    }

    private Vector3 Refract(Vector3 I, Vector3 N, float eta)
    {
        float k = 1.0f - eta * eta * (1.0f - Vector3.Dot(N, I) * Vector3.Dot(N, I));
        if (k < 0.0f) return Vector3.Zero; // Total internal reflection
        return eta * I - (eta * Vector3.Dot(N, I) + MathF.Sqrt(k)) * N;
    }
}

// =========================================================
// MAIN PROGRAM
// =========================================================

class Program
{
    const int Width = 800;
    const int Height = 600;

    static void Main()
    {
        Raylib.InitWindow(Width, Height, "C# Ray Tracer - Raylib - .NET 8");
        Raylib.SetTargetFPS(60);

        // Buffer for raw pixel data (RGBA, 4 bytes per pixel)
        byte[] pixelData = new byte[Width * Height * 4];

        // Raylib Image and Texture setup
        Image image = Raylib.GenImageColor(Width, Height, Color.Black);
        Texture2D texture = Raylib.LoadTextureFromImage(image);
        Raylib.UnloadImage(image); // Texture is on GPU now, we update it via buffer

        RayTracer tracer = new RayTracer();
        tracer.InitScene();

        // Camera setup
        Vector3 camPos = new Vector3(0, 0, -5);

        while (!Raylib.WindowShouldClose())
        {
            // 1. Input
            tracer.UpdateInput();

            // 2. Render (Ray Tracing) in Parallel
            // Using unsafe to write directly to the byte array is faster, but span is safer.
            Parallel.For(0, Height, y =>
            {
                for (int x = 0; x < Width; x++)
                {
                    // Map x,y to normalized device coordinates (-1 to 1)
                    float u = (x / (float)Width) * 2.0f - 1.0f;
                    float v = (y / (float)Height) * 2.0f - 1.0f;

                    // Aspect ratio correction
                    u *= (float)Width / Height;
                    // Flip Y because screens are Top-Left 0,0 but 3D is usually Bottom-Left
                    v *= -1.0f;

                    Vector3 rayDir = Vector3.Normalize(new Vector3(u, v, 2.0f)); // 2.0f is focal length
                    Ray ray = new Ray(camPos, rayDir);

                    // Trace
                    Vector3 col = tracer.Trace(ray, 5);

                    // Tone Mapping & Gamma Correction
                    col = Vector3.Clamp(col, Vector3.Zero, Vector3.One);
                    // Simple Gamma 2.2 approximate (sqrt is Gamma 2.0, close enough for real-time)
                    col.X = MathF.Sqrt(col.X);
                    col.Y = MathF.Sqrt(col.Y);
                    col.Z = MathF.Sqrt(col.Z);

                    // Write to buffer
                    int index = (y * Width + x) * 4;
                    pixelData[index] = (byte)(col.X * 255);
                    pixelData[index + 1] = (byte)(col.Y * 255);
                    pixelData[index + 2] = (byte)(col.Z * 255);
                    pixelData[index + 3] = 255; // Alpha
                }
            });

            // 3. Update GPU Texture
            Raylib.UpdateTexture(texture, pixelData);

            // 4. Draw
            Raylib.BeginDrawing();
            Raylib.ClearBackground(Color.Black);

            // Draw texture stretched to screen (source rect, dest rect, origin, rotation, tint)
            Raylib.DrawTexture(texture, 0, 0, Color.White);

            Raylib.DrawText("Controls: [Arrows] Light | [M] Mirror | [T] Transparent | [W] Back Wall Mirror | [Space] Add Obj", 10, 10, 10, Color.White);
            Raylib.DrawText($"FPS: {Raylib.GetFPS()}", 10, 30, 10, Color.Green);

            Raylib.EndDrawing();
        }

        Raylib.UnloadTexture(texture);
        Raylib.CloseWindow();
    }
}