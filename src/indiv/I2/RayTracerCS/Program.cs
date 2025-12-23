using System.Collections.Concurrent;
using System.Diagnostics;
using System.Numerics;
using Raylib_cs;

// =========================================================
// MATH & STRUCTURES
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
    public Vector3 Albedo;
    public float Specular;
    public float Smoothness;
    public float Reflectivity;
    public float Transparency;
    public float IOR;

    public static Material Lambert(Vector3 color) => new() {
        Albedo = color,
        Specular = 0.0f,
        IOR = 1.0f
    };

    // Металл должен сильно отражать и иметь слабый собственный цвет
    public static Material Metal(Vector3 color, float fuzz) => new() {
        Albedo = color,
        Specular = 1.0f,
        Smoothness = 200f,
        Reflectivity = 0.95f - fuzz,
        IOR = 1.0f
    };

    // Стекло: Albedo почти черный (все уходит в преломление), Specular высокий (блики)
    public static Material Glass(float ior) => new() {
        Albedo = new Vector3(0.05f),
        Specular = 1.0f,
        Smoothness = 300f,
        Reflectivity = 0.1f,
        Transparency = 0.95f,
        IOR = ior
    };
}

public struct Light
{
    public Vector3 Position;
    public Vector3 Color;
    public float Intensity;
}

// =========================================================
// SCENE OBJECTS
// =========================================================

public abstract class SceneObject
{
    public string Name = "Object";
    public Vector3 Position;
    public Material Mat;
    public Vector3 BaseColor;

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
        if (dist < 0.001f) dist = (-b + MathF.Sqrt(discriminant)) / (2.0f * a);
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
    public Vector3 Size;

    public override bool Intersect(Ray ray, out HitInfo hit)
    {
        hit = new HitInfo();
        Vector3 min = Position - Size;
        Vector3 max = Position + Size;

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

        if (tMax < tMin || tMax < 0) return false;
        float finalDist = tMin > 0.001f ? tMin : tMax;
        if (finalDist < 0.001f || float.IsNaN(finalDist)) return false;

        hit.DidHit = true;
        hit.Distance = finalDist;
        hit.Point = ray.Origin + ray.Direction * finalDist;
        hit.Mat = Mat;

        Vector3 p = hit.Point - Position;
        Vector3 d = new Vector3(MathF.Abs(p.X) / Size.X, MathF.Abs(p.Y) / Size.Y, MathF.Abs(p.Z) / Size.Z);

        Vector3 normal = Vector3.Zero;
        if (d.X > d.Y && d.X > d.Z) normal = new Vector3(SafeSign(p.X), 0, 0);
        else if (d.Y > d.Z) normal = new Vector3(0, SafeSign(p.Y), 0);
        else normal = new Vector3(0, 0, SafeSign(p.Z));

        hit.Normal = Vector3.Normalize(normal);
        return true;
    }

    private float SafeSign(float value) => float.IsNaN(value) ? 0 : (value >= 0 ? 1.0f : -1.0f);
}

// =========================================================
// RAY TRACER ENGINE
// =========================================================

public class RayTracer
{
    public List<SceneObject> Objects = new();
    public List<Light> Lights = new();

    // State
    public SceneObject? SelectedObject = null;

    // Camera settings (for mouse picking)
    public Vector3 CamPos = new Vector3(0, 0, -2f);
    public float FOV_Factor = 1.0f; // Focal length roughly (POV factor)

    public void InitScene()
    {
        Objects.Clear();
        Lights.Clear();

        // Room
        float roomSize = 2.0f;
        float thickness = 0.1f;
        Objects.Add(new Cube {
            Name="Floor",
            Position = new Vector3(0, -roomSize - thickness, 0),
            Size = new Vector3(roomSize, thickness, roomSize),
            Mat = Material.Lambert(new Vector3(1.0f))
        });
        Objects.Add(new Cube {
            Name="Ceiling",
            Position = new Vector3(0, roomSize + thickness, 0),
            Size = new Vector3(roomSize, thickness, roomSize),
            Mat = Material.Lambert(new Vector3(1.0f))
        });
        Objects.Add(new Cube {
            Name="BackWall",
            Position = new Vector3(0, 0, roomSize + thickness),
            Size = new Vector3(roomSize, roomSize, thickness),
            Mat = Material.Lambert(new Vector3(1.0f))
        });
        Objects.Add(new Cube {
            Name="LeftWall",
            Position = new Vector3(-roomSize - thickness, 0, 0),
            Size = new Vector3(thickness, roomSize, roomSize),
            Mat = Material.Lambert(new Vector3(1.0f, 0.2f, 0.2f))
        });
        Objects.Add(new Cube {
            Name="RightWall",
            Position = new Vector3(roomSize + thickness, 0, 0),
            Size = new Vector3(thickness, roomSize, roomSize),
            Mat = Material.Lambert(new Vector3(0.2f, 1.0f, 0.2f))
        });
        Objects.Add(new Cube {
            Name="FrontWall",
            Position = new Vector3(0, 0, -roomSize - thickness), //Position = new Vector3(0, 0, -6.0f), если пофиг на дыркуы
            Size = new Vector3(roomSize, roomSize, thickness),
            // Mat = Material.Metal(new Vector3(0.2f, 0.2f, 1.0f), 0.0f) //
            Mat = Material.Lambert(new Vector3(0.2f, 1.0f, 1.0f)) // Синяя задняя стена
        });

        // Initial Objects
        Objects.Add(new Sphere {
            Name="Sphere1",
            Position = new Vector3(-0.8f, -1.0f, 0.5f),
            Radius = 0.8f,
            Mat = Material.Lambert(new Vector3(0.2f, 0.5f, 0.9f))
        });
        Objects.Add(new Cube {
            Name="Cube1",
            Position = new Vector3(1.0f, -1.2f, 0.3f),
            Size = new Vector3(0.6f, 0.8f, 0.6f),
            Mat = Material.Metal(new Vector3(0.9f, 0.8f, 0.2f), 0.1f)
        });
        Objects.Add(new Sphere {
            Name="Sphere2",
            Position = new Vector3(1.0f, 0.0f, 0.3f),
            Radius = 0.3f,
            Mat = Material.Lambert(new Vector3(0.2f, 0.5f, 0.9f))
        });

        // Default Light
        Lights.Add(new Light { Position = new Vector3(0, 1.8f, 0), Color = Vector3.One, Intensity = 1.2f });
    }

    public float GetRandomFloatBetween(float min, float max) {
        return min + (max - min) * (float)Random.Shared.NextDouble();
    }

    // Helper to generate a ray from screen coordinates (for rendering AND mouse picking)
    public Ray GetCameraRay(float x, float y, int screenWidth, int screenHeight)
    {
        // float u = ((x + GetRandomFloatBetween(-0.5f, 0.5f)) / (float)screenWidth) * 2.0f - 1.0f;
        // float v = ((y + GetRandomFloatBetween(-0.5f, 0.5f)) / (float)screenHeight) * 2.0f - 1.0f;
        float u = (x / (float)screenWidth) * 2.0f - 1.0f;
        float v = (y / (float)screenHeight) * 2.0f - 1.0f;

        u *= (float)screenWidth / screenHeight;
        v *= -1.0f; // Flip Y


        Vector3 dir = Vector3.Normalize(new Vector3(u, v, FOV_Factor));
        return new Ray(CamPos, dir);
    }

    public void UpdateInput(int width, int height)
    {
        // 1. Mouse Picking (Select Object)
        if (Raylib.IsMouseButtonPressed(MouseButton.Left))
        {
            Vector2 mouse = Raylib.GetMousePosition();
            Ray mouseRay = GetCameraRay(mouse.X, mouse.Y, width, height);

            if (GetClosestHit(mouseRay, out HitInfo hit, out SceneObject? hitObj))
            {
                SelectedObject = hitObj;
                Console.WriteLine($"Selected: {hitObj?.Name}");
            }
            else
            {
                SelectedObject = null;
            }
        }

        // 2. Add Objects
        var rand = new Random();
        if (Raylib.IsKeyPressed(KeyboardKey.One))
        {
            float r = (float)rand.NextDouble() * 0.4f + 0.2f;
            Vector3 pos = new Vector3((float)rand.NextDouble()*2-1, (float)rand.NextDouble()*2-1, 0);
            Vector3 col = new Vector3((float)rand.NextDouble(), (float)rand.NextDouble(), (float)rand.NextDouble());
            Objects.Add(new Sphere { Name="GenSphere", Position = pos, Radius = r, Mat = Material.Lambert(col), BaseColor = col });
        }
        if (Raylib.IsKeyPressed(KeyboardKey.Two))
        {
            float s = (float)rand.NextDouble() * 0.4f + 0.2f;
            Vector3 pos = new Vector3((float)rand.NextDouble()*2-1, (float)rand.NextDouble()*2-1, 0);
            Vector3 col = new Vector3((float)rand.NextDouble(), (float)rand.NextDouble(), (float)rand.NextDouble());
            Objects.Add(new Cube { Name="GenCube", Position = pos, Size = new Vector3(s,s,s), Mat = Material.Lambert(col), BaseColor = col });
        }

        // 3. Add Light
        if (Raylib.IsKeyPressed(KeyboardKey.L))
        {
             Lights.Add(new Light {
                 Position = new Vector3(0, 0, -1.0f),
                 // Color = new Vector3((float)rand.NextDouble(), (float)rand.NextDouble(), (float)rand.NextDouble()),
                 Color = new Vector3(1.0f, 0.0f, 1.0f),
                 Intensity = 1.0f
             });
        }

        // 4. Modify Selection
        if (SelectedObject != null)
        {
            if (Raylib.IsKeyPressed(KeyboardKey.Delete)) Objects.Remove(SelectedObject);

            if (Raylib.IsKeyPressed(KeyboardKey.M)) // Toggle Mirror
            {
                if (SelectedObject.Mat.Reflectivity > 0)
                {
                    // Object has no BaseColor
                    if (SelectedObject.BaseColor == Vector3.Zero) SelectedObject.BaseColor = SelectedObject.Mat.Albedo;

                    SelectedObject.Mat = Material.Lambert(SelectedObject.BaseColor);
                }
                else
                {
                    if (SelectedObject.Mat.Albedo.Length() > 0.1f) SelectedObject.BaseColor = SelectedObject.Mat.Albedo;

                    SelectedObject.Mat = Material.Metal(Vector3.One, 0.0f);
                }
            }

            if (Raylib.IsKeyPressed(KeyboardKey.T)) // Toggle Transparent
            {
                if (SelectedObject.Mat.Transparency > 0)
                {
                    if (SelectedObject.BaseColor == Vector3.Zero) SelectedObject.BaseColor = new Vector3(0.5f); // Дефолтный серый, если потеряли
                    SelectedObject.Mat = Material.Lambert(SelectedObject.BaseColor);
                }
                else
                {
                    if (SelectedObject.Mat.Albedo.Length() > 0.1f) SelectedObject.BaseColor = SelectedObject.Mat.Albedo;
                    SelectedObject.Mat = Material.Glass(1.05f); // 1.5
                }
            }
        }

        // 5. Move Last Light
        if (Lights.Count > 0)
        {
            float speed = 0.1f;
            var lastLight = Lights[^1];
            if (Raylib.IsKeyDown(KeyboardKey.Left)) lastLight.Position.X -= speed;
            if (Raylib.IsKeyDown(KeyboardKey.Right)) lastLight.Position.X += speed;
            if (Raylib.IsKeyDown(KeyboardKey.Up)) lastLight.Position.Z -= speed;
            if (Raylib.IsKeyDown(KeyboardKey.Down)) lastLight.Position.Z += speed;
            if (Raylib.IsKeyDown(KeyboardKey.KpAdd)) lastLight.Position.Y += speed;
            if (Raylib.IsKeyDown(KeyboardKey.KpSubtract)) lastLight.Position.Y -= speed;
            Lights[^1] = lastLight;
        }
    }

    private Vector3 GetDiffuseReflection(Vector3 normal){
        float x = (float)Random.Shared.NextDouble() * 0.2f - 0.1f;
        float y = (float)Random.Shared.NextDouble() * 0.2f - 0.1f;
        float z = (float)Random.Shared.NextDouble() * 0.2f - 0.1f;
        Vector3 rnd = Vector3.Normalize(new Vector3(x, y, z));
        return Vector3.Normalize(normal + 0.5f * rnd);
    }

    public Vector3 Trace(Ray ray, int depth)
    {
        if (depth <= 0) return Vector3.Zero;

        if (!GetClosestHit(ray, out HitInfo hit, out SceneObject? hitObj)) return Vector3.Zero;

        Vector3 finalColor = Vector3.Zero;

        // === 1. Local Lighting (Phong) ===
        // Для прозрачных объектов диффузный свет считаем слабее, иначе стекло выглядит как пластик
        float lightingContribution = 1.0f - hit.Mat.Transparency;

        if (lightingContribution > 0.01f)
        {
            bool ENABLE_DIFFUSE_REFLECTION = false;
            if ((depth > 2) && (ENABLE_DIFFUSE_REFLECTION)){
                Vector3 giDir = GetDiffuseReflection(hit.Normal);
                Ray giRay = new Ray(hit.Point + hit.Normal * 0.005f, giDir);

                Vector3 indirectColor = Trace(giRay, depth - 2);

                finalColor += hit.Mat.Albedo * indirectColor * 0.3f * lightingContribution;
            }
            else {
                finalColor += hit.Mat.Albedo * 0.05f * lightingContribution;
            }

            // Ambient
            // finalColor += hit.Mat.Albedo * 0.05f * lightingContribution;

            foreach (var light in Lights)
            {
                Vector3 lightDir = Vector3.Normalize(light.Position - hit.Point);
                float distToLight = Vector3.Distance(light.Position, hit.Point);

                // Shadow Ray (смещаем в сторону света, чтобы не попасть в себя)
                Ray shadowRay = new Ray(hit.Point + hit.Normal * 0.005f, lightDir);

                bool inShadow = false;
                if (GetClosestHit(shadowRay, out HitInfo sHit, out SceneObject? sObj))
                {
                    // Если препятствие есть, и оно непрозрачное -> тень
                    if (sHit.Distance < distToLight && sHit.Mat.Transparency < 0.9f)
                        inShadow = true;
                }

                if (!inShadow)
                {
                    // Diffuse
                    float NdotL = MathF.Max(0, Vector3.Dot(hit.Normal, lightDir));
                    Vector3 diffuse = hit.Mat.Albedo * light.Color * NdotL * light.Intensity * lightingContribution;

                    // Specular (Блики стекла)
                    Vector3 viewDir = Vector3.Normalize(-ray.Direction);
                    Vector3 halfVector = Vector3.Normalize(lightDir + viewDir);
                    float NdotH = MathF.Max(0, Vector3.Dot(hit.Normal, halfVector));
                    float specFactor = MathF.Pow(NdotH, hit.Mat.Smoothness > 0 ? hit.Mat.Smoothness : 1.0f);
                    Vector3 specular = light.Color * hit.Mat.Specular * specFactor * light.Intensity;

                    finalColor += diffuse + specular;
                }
            }
        }

        // === 2. Reflection (Mirror) ===
        if (hit.Mat.Reflectivity > 0.0f)
        {
            Vector3 reflectDir = Vector3.Reflect(ray.Direction, hit.Normal);
            Ray reflectRay = new Ray(hit.Point + hit.Normal * 0.005f, reflectDir); // bias
            finalColor += Trace(reflectRay, depth - 1) * hit.Mat.Reflectivity;
        }

        // === 3. Refraction (Glass) ===
        if (hit.Mat.Transparency > 0.0f)
        {
            float eta = 1.0f / hit.Mat.IOR;
            Vector3 normal = hit.Normal;

            // Определение: входим мы или выходим
            if (Vector3.Dot(ray.Direction, normal) > 0)
            {
                normal = -normal; // Выходим из объекта
                eta = hit.Mat.IOR;
            }

            Vector3 refractDir;
            bool canRefract = Refract(ray.Direction, normal, eta, out refractDir);

            if (canRefract)
            {
                // Проходим сквозь
                // Bias внутрь объекта (вычитаем нормаль)
                Ray refractRay = new Ray(hit.Point - normal * 0.005f, refractDir);
                Vector3 refractColor = Trace(refractRay, depth - 1);
                // Смешиваем по закону Френеля (линейно)
                finalColor = Vector3.Lerp(finalColor, refractColor, hit.Mat.Transparency);
            }
            else
            {
                // Total Internal Reflection (Полное внутреннее отражение)
                Vector3 reflectDir = Vector3.Reflect(ray.Direction, normal);
                Ray internalRay = new Ray(hit.Point + normal * 0.005f, reflectDir);
                finalColor += Trace(internalRay, depth - 1) * hit.Mat.Transparency;
            }
        }

        return finalColor;
    }

    private bool Refract(Vector3 I, Vector3 N, float eta, out Vector3 refractDir)
    {
        float dotNI = Vector3.Dot(N, I);
        float k = 1.0f - eta * eta * (1.0f - dotNI * dotNI);

        if (k < 0.0f)
        {
            refractDir = Vector3.Zero;
            return false; // Total Internal Reflectio
        }

        refractDir = eta * I - (eta * dotNI + MathF.Sqrt(k)) * N;
        return true;
    }

    private bool GetClosestHit(Ray ray, out HitInfo bestHit, out SceneObject? hitObj)
    {
        bestHit = new HitInfo { Distance = float.MaxValue };
        hitObj = null;
        bool didHit = false;

        foreach (var obj in Objects)
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

}

class Program
{
    const int Width = 800;
    const int Height = 600;

    static void Main()
    {
        Raylib.InitWindow(Width, Height, "C# Ray Tracer - Advanced");
        Raylib.SetTargetFPS(60);

        byte[] pixelData = new byte[Width * Height * 4];
        Image image = Raylib.GenImageColor(Width, Height, Color.Black);
        Texture2D texture = Raylib.LoadTextureFromImage(image);
        Raylib.UnloadImage(image);

        RayTracer tracer = new RayTracer();
        tracer.InitScene();

        while (!Raylib.WindowShouldClose())
        {
            tracer.UpdateInput(Width, Height);

            Parallel.For(0, Height, y =>
            // for (int y = 0; y < Height; y++)
            {
                for (int x = 0; x < Width; x++)
                {
                    int samplesCount = 1;
                    Vector3 color = Vector3.Zero;
                    for (int s = 0; s < samplesCount; s++) {
                        Ray ray = tracer.GetCameraRay(x, y, Width, Height);
                        Vector3 col = tracer.Trace(ray, 4); // Depth 4 for speed

                        // Tone Mapping
                        col = col / (col + Vector3.One); // Reinhard
                        col = Vector3.Clamp(col, Vector3.Zero, Vector3.One);

                        // Gamma
                        col.X = MathF.Sqrt(col.X);
                        col.Y = MathF.Sqrt(col.Y);
                        col.Z = MathF.Sqrt(col.Z);

                        color += col;
                    }

                    color /= samplesCount;

                    int index = (y * Width + x) * 4;
                    pixelData[index] = (byte)(color.X * 255);
                    pixelData[index + 1] = (byte)(color.Y * 255);
                    pixelData[index + 2] = (byte)(color.Z * 255);
                    pixelData[index + 3] = 255;
                }
            });

            Raylib.UpdateTexture(texture, pixelData);

            Raylib.BeginDrawing();
            Raylib.ClearBackground(Color.Black);
            Raylib.DrawTexture(texture, 0, 0, Color.White);

            // UI Overlay
            Raylib.DrawRectangle(5, 5, 400, 110, new Color(0, 0, 0, 150));
            Raylib.DrawText("CONTROLS:", 10, 10, 20, Color.Yellow);
            Raylib.DrawText("[L-Click] Select Object | [DEL] Delete", 10, 35, 10, Color.White);
            Raylib.DrawText("[1] Add Sphere | [2] Add Cube | [L] Add Light", 10, 50, 10, Color.White);
            Raylib.DrawText("[M] Toggle Mirror | [T] Toggle Transparency", 10, 65, 10, Color.White);
            Raylib.DrawText("[Arrows] Move Last Light | [+/-] Light Up/Down", 10, 80, 10, Color.White);

            string selName = tracer.SelectedObject != null ? tracer.SelectedObject.Name : "None";
            Raylib.DrawText($"Selected: {selName} | Lights: {tracer.Lights.Count}", 10, 95, 10, Color.Green);

            Raylib.DrawFPS(Width - 80, 10);

            Raylib.EndDrawing();
        }

        Raylib.UnloadTexture(texture);
        Raylib.CloseWindow();
    }
}