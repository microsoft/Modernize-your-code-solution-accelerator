import React, { useState, useEffect, ReactNode, ReactElement } from "react";
import eventBus from "../common/eventbus.js";
import PanelRightToolbar from "./PanelRightToolbar"; // Import to identify toolbar
import "./Panels.scss"

interface PanelRightProps {
  panelWidth?: number; // Optional width of the panel
  panelResize?: boolean; // Whether resizing is enabled
  panelType: "first" | "second" | "third" | "fourth"; // Panel type identifier
  children?: ReactNode;
}

const PanelRight: React.FC<PanelRightProps> = ({
  panelWidth = 325, // Default width if not provided
  panelResize = true,
  panelType = "first", // Default to "first" if not explicitly defined
  children,
}) => {
  const [isActive, setIsActive] = useState(panelType === "first"); // Initialize based on the panelType
  const [width, setWidth] = useState<number>(panelWidth); // Initial width from props or default
  const [isHandleHovered, setIsHandleHovered] = useState(false);

  useEffect(() => {
    // Initialize shared width if not already set in the EventBus
    if (eventBus.getPanelWidth() === 400) {
      eventBus.setPanelWidth(panelWidth); // Use the provided panelWidth prop
    } 
    setWidth(eventBus.getPanelWidth()); // Set the current width from EventBus

    const handleActivePanel = (panel: "first" | "second" | "third" | "fourth" | null) => {
      setIsActive(panel === panelType); // Check if this panelType matches the active panel
    };

    const handleWidthChange = (newWidth: number) => {
      setWidth(newWidth); // Update width when EventBus notifies
    };

    eventBus.on("setActivePanel", handleActivePanel);
    eventBus.on("panelWidthChanged", handleWidthChange);

    return () => {
      eventBus.off("setActivePanel", handleActivePanel);
      eventBus.off("panelWidthChanged", handleWidthChange);
    };
  }, [panelType, panelWidth]);

  const handleMouseDown = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!panelResize) return;

    const startX = e.clientX;
    const startWidth = width;

    const onMouseMove = (moveEvent: MouseEvent) => {
      const newWidth = Math.min(
        500, // Max width
        Math.max(256, startWidth - (moveEvent.clientX - startX)) // Min width
      );
      setWidth(newWidth);
      eventBus.setPanelWidth(newWidth); // Persist the new width in EventBus
    };

    const onMouseUp = () => {
      document.removeEventListener("mousemove", onMouseMove);
      document.removeEventListener("mouseup", onMouseUp);
      document.body.style.userSelect = "";
    };

    document.addEventListener("mousemove", onMouseMove);
    document.addEventListener("mouseup", onMouseUp);

    document.body.style.userSelect = "none";
  };

  if (!isActive) return null; // Do not render if not active

  const childrenArray = React.Children.toArray(children) as ReactElement[];
  const toolbar = childrenArray.find(
    (child) => React.isValidElement(child) && child.type === PanelRightToolbar
  );
  const content = childrenArray.filter(
    (child) => !(React.isValidElement(child) && child.type === PanelRightToolbar)
  );

  return (
    <div
      className="panels"
      style={{
        width: `${width}px`,
        borderLeft: panelResize
          ? isHandleHovered
            ? "2px solid var(--colorNeutralStroke2)"
            : "2px solid transparent"
          : "none",
      }}
    >
      {toolbar && <div className="fs_0">{toolbar}</div>}

      <div
        className="panelContent content2"
      >
        {content}
      </div>

      {panelResize && (
        <div
          className="resizeHandle"
          onMouseDown={handleMouseDown}
          onMouseEnter={() => setIsHandleHovered(true)}
          onMouseLeave={() => setIsHandleHovered(false)}
          style={{
            backgroundColor: isHandleHovered
              ? "var(--colorNeutralStroke2)"
              : "transparent",
          }}
        />
      )}
    </div>
  );
};

export default PanelRight;
