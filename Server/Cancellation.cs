namespace mahl.Server;

internal static class Cancellation
{
    // Bewusst ohne RequestAborted: Das Backend reicht Abbruch nirgends durch (Sonar S8949 verlangt die explizite Wahl).
    // Einzige Stelle dieser Wahl – wo ein Aufruf den Token ausdrücklich übergibt, nimmt er diesen.
    internal static readonly CancellationToken None = CancellationToken.None;
}
