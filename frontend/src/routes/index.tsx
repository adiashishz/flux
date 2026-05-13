import { createBrowserRouter, Navigate } from "react-router-dom"
import { AppLayout } from "@/components/layout/AppLayout"
import { BoardList } from "@/features/board/BoardList"
import { BoardView } from "@/features/board/BoardView"
import { WorkspaceList } from "@/features/workspace/WorkspaceList"

export const router = createBrowserRouter([
  {
    path: "/",
    element: <AppLayout />,
    children: [
      { index: true, element: <Navigate to="/boards" replace /> },
      { path: "boards", element: <BoardList /> },
      { path: "boards/:id", element: <BoardView /> },
      { path: "workspaces", element: <WorkspaceList /> },
      { path: "workspaces/:workspaceId", element: <BoardList /> },
      { path: "workspaces/:workspaceId/boards/:id", element: <BoardView /> },
    ],
  },
])
